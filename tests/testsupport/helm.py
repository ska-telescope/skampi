import glob
import os
import random
import string
import subprocess


class HelmTestAdaptor(object):
    HELM_TEMPLATE_CMD = "helm template --namespace {} --name {} -x templates/{} charts/{}"
    HELM_DELETE_CMD = "helm delete {} --purge"
    HELM_INSTALL_CMD = "helm install charts/{} --namespace {} --wait"

    def __init__(self, use_tiller_plugin, test_namespace):
        self.use_tiller_plugin = use_tiller_plugin
        self.namespace = test_namespace

    def install(self, chart):
        cmd = self._wrap_tiller(self.HELM_INSTALL_CMD.format(chart, self.namespace))
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
    def __init__(self, chart, helm_adaptor, k8s_api):
        self._helm_adaptor = helm_adaptor
        self._k8s_api = k8s_api

        try:
            stdout = self._helm_adaptor.install(chart)  # actual deployment

            self.chart_name = chart
            self.release_name = self._parse_release_name_from(stdout)
        except Exception as e:
            raise RuntimeError('!!! Failed to deploy helm chart.', e)

    def delete(self):
        assert self.release_name is not None
        self._helm_adaptor.delete(self.release_name)

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

    def _get_pods_by_release_name_in_pod_name(self, api_instance, pod_list):
        all_namespaced_pods = api_instance.list_namespaced_pod(self._helm_adaptor.namespace).items
        pod_list = [pod for pod in all_namespaced_pods if
                    pod.metadata.name.index(self.release_name) > -1]
        return pod_list

    def _get_pods_by_release_name_in_label(self, api_instance):
        pod_list = api_instance.list_namespaced_pod(self._helm_adaptor.namespace,
                                                    label_selector="release={}".format(self.release_name)).items
        return pod_list

    def _get_pods_by_pod_name(self, api_instance, pod_name):
        return api_instance.list_namespaced_pod(self._helm_adaptor.namespace,
                                                field_selector="metadata.name={}".format(pod_name)).items

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
