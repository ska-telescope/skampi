import glob
import os
import random
import string
import subprocess
import logging


class HelmTestAdaptor(object):
    HELM_TEMPLATE_CMD = "helm template --namespace {} --name {} -x templates/{} charts/{}"
    HELM_DELETE_CMD = "helm delete {} --purge"
    HELM_INSTALL_CMD = "helm install charts/{} --namespace {} --wait {}"

    def __init__(self, use_tiller_plugin, test_namespace):
        self.use_tiller_plugin = use_tiller_plugin
        self.namespace = test_namespace

    def install(self, chart, cmd_args=""):
        cmd = self._wrap_tiller(self.HELM_INSTALL_CMD.format(chart, self.namespace, cmd_args))
        cmd = cmd.split()
        return self._run_subprocess(cmd)

    def delete(self, helm_release):
        cmd = self._wrap_tiller(self.HELM_DELETE_CMD.format(helm_release))
        return self._run_subprocess(cmd.split())

    def template(self, chart_name, release_name, template):
        cmd = self.HELM_TEMPLATE_CMD.format(self.namespace, release_name, template, chart_name)
        return self._run_subprocess(cmd.split())

    def _wrap_tiller(self, helm_cmd):
        if self.use_tiller_plugin is True:
            cli_cmd = self.__prefix_cmd_with_tiller_run(helm_cmd)
        else:
            cli_cmd = helm_cmd
        return cli_cmd

    @staticmethod
    def _run_subprocess(shell_cmd):
        result = subprocess.run(shell_cmd, stdout=subprocess.PIPE, encoding="utf8", check=True)
        return result.stdout

    @staticmethod
    def __prefix_cmd_with_tiller_run(helm_cmd):
        HELM_TILLER_PREFIX = "helm tiller run -- "
        deploy_cmd = (HELM_TILLER_PREFIX + helm_cmd)
        return deploy_cmd


class ChartDeployment(object):
    def __init__(self, chart, helm_adaptor, k8s_api, values={}):
        self._helm_adaptor = helm_adaptor
        self._k8s_api = k8s_api

        try:
            set_flag = ChartDeployment.create_set_cli_flag_from(values)
            stdout = self._helm_adaptor.install(chart, set_flag)  # actual deployment

            self.chart_name = chart
            self.release_name = self._parse_release_name_from(stdout)
        except Exception as e:
            raise RuntimeError('!!! Failed to deploy helm chart.', e)

    def delete(self):
        assert self.release_name is not None
        api_instance = self._k8s_api.CoreV1Api()
        p_volumes = self._get_persistent_volume_names(api_instance)
        logging.info("Persistent Volumes to delete: %s", p_volumes)

        self._helm_adaptor.delete(self.release_name)

        for pv in p_volumes:
            # Make double sure we only delete PVs in our release
            if self.release_name in pv:
                api_instance.delete_persistent_volume(pv)
                logging.info("Deleted PV: %s", pv)


    def pod_exec_bash(self, pod_name, command_str):
        """Execute a command on the pod commandline using bash

        Parameters
        ----------
        pod_name : string
            The name of the pod to execute the command in
        command_str : string
            The command to execute.
            E.g passing in `ls -l` will result in `/bin/bash -c ls -l` being executed

        Returns
        -------
        string
            The result of the command
        """
        cmd = ['kubectl', 'exec', '-n', self._helm_adaptor.namespace, pod_name,
               '--', '/bin/bash', '-c', command_str]
        logging.info(cmd)
        res = self._helm_adaptor._run_subprocess(cmd)
        return res


    def get_pods(self, pod_name=None):
        api_instance = self._k8s_api.CoreV1Api()

        if pod_name:
            return self._get_pods_by_pod_name(api_instance, pod_name)

        pod_list = self._get_pods_by_release_name_in_label(api_instance)
        no_pods_with_release_label = len(pod_list) == 0

        # TODO enforce a mininum standard set of metadata labels
        # e.g.  https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/#labels
        if no_pods_with_release_label:
            pod_list = self._get_pods_by_release_name_in_pod_name(api_instance, pod_list)

        return pod_list

    def search_pod_name(self, term):
        """Searches the pod names that contains the term

        Parameters
        ----------
        term : string
            The search term to search for

        Returns
        -------
        list
            The list of pod names that contains the term
        """
        pods = self.get_pods()
        pods = [pod.to_dict() for pod in pods]
        all_pod_names = [pod['metadata']['name'] for pod in pods]
        searched_pod_names = [pod_name for pod_name in all_pod_names if term in pod_name]
        return searched_pod_names

    def _get_pods_by_release_name_in_pod_name(self, api_instance, pod_list):
        all_namespaced_pods = api_instance.list_namespaced_pod(self._helm_adaptor.namespace).items
        pod_list = [pod for pod in all_namespaced_pods
                    if self.release_name in pod.metadata.name]
        return pod_list

    def _get_pods_by_release_name_in_label(self, api_instance):
        pod_list = api_instance.list_namespaced_pod(self._helm_adaptor.namespace,
                                                    label_selector="release={}".format(self.release_name)).items
        return pod_list

    def _get_pods_by_pod_name(self, api_instance, pod_name):
        return api_instance.list_namespaced_pod(self._helm_adaptor.namespace,
                                                field_selector="metadata.name={}".format(pod_name)).items

    def _get_persistent_volume_names(self, api_instance):
        ns = self._helm_adaptor.namespace
        pvcs = api_instance.list_namespaced_persistent_volume_claim(namespace=ns)
        pvcs = pvcs.to_dict()
        p_volumes = []
        if 'items' in pvcs:
            p_volumes = [i['spec']['volume_name'] for i in pvcs['items']]
        return p_volumes

    def is_running(self, pod_name):
        pod_list = self.get_pods(pod_name)
        assert len(pod_list) == 1
        pod = pod_list.pop()
        return pod.status.phase == 'Running'

    def get_services(self):
        api_instance = self._k8s_api.CoreV1Api()
        return [svc for svc in api_instance.list_namespaced_service(self._helm_adaptor.namespace).items if
                svc.metadata.name.endswith(self.release_name)]

    @staticmethod
    def create_set_cli_flag_from(values):
        chart_values = [f"{key}={value}" for key, value in values.items()]
        set_flag = "--set={}".format(",".join(chart_values))
        return set_flag

    @staticmethod
    def _parse_release_name_from(stdout):
        release_name_line = ''.join(l for l in stdout.split('\n') if l.startswith('NAME:'))
        return release_name_line.split().pop()


class HelmChart(object):

    def __init__(self, name, helm_adaptor):
        self.name = name
        self.templates_dir = "charts/{}/templates".format(self.name)
        self._helm_adaptor = helm_adaptor
        self._release_name_stub = self.generate_release_name()
        self._rendered_templates = None

    @property
    def templates(self):
        if self._rendered_templates is not None:
            return self._rendered_templates

        chart_templates = [os.path.basename(fpath) for fpath in (glob.glob("{}/*.yaml".format(self.templates_dir)))]
        self._rendered_templates = {template: self._helm_adaptor.template(self.name, self._release_name_stub, template)
                                    for template in
                                    chart_templates}
        return self._rendered_templates

    def render_template(self, template_file, release_name):
        return self._helm_adaptor.template(self.name, release_name, os.path.join(self.templates_dir, template_file))

    @staticmethod
    def generate_release_name():
        def random_alpha(length=7):
            return ''.join(random.choices(string.ascii_lowercase, k=length))

        return "{}-{}".format(random_alpha(), random_alpha())
