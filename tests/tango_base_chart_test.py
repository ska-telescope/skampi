import subprocess
import collections

import pytest
import testinfra
import yaml

from io import StringIO

class HelmTestAdaptor(object):
    HELM_TEMPLATE_CMD = "helm template --name {} -x templates/{} charts/{}"
    HELM_DELETE_CMD = "helm delete {} --purge"
    HELM_INSTALL_CMD = "helm install charts/{} --namespace ci --wait"

    def __init__(self, chart_name, use_tiller_plugin):
        self.chart_name = chart_name
        self.use_tiller_plugin = use_tiller_plugin

    def deploy_chart(self):
        cmd_stdout = self.run_cmd(self.HELM_INSTALL_CMD.format(self.chart_name))
        return self._parse_helm_release_name_from(cmd_stdout)

    def undeploy_chart(self, helm_release):
        self.run_cmd(self.HELM_DELETE_CMD.format(helm_release))

    def render_template(self, release_name, template):
        return self.run_cmd(HelmTestAdaptor.HELM_TEMPLATE_CMD.format(release_name, template, self.chart_name))

    def _parse_helm_release_name_from(self, stdout):
        release_name_line = ''.join(l for l in stdout.split('\n') if l.startswith('NAME:'))
        release_name = release_name_line.split().pop()
        return release_name

    def run_cmd(self, helm_cmd):
        if self.use_tiller_plugin is True:
            deploy_cmd = self.prefix_cmd_with_tiller_run(helm_cmd)
        else:
            deploy_cmd = helm_cmd.split()
        cmd_stdout = self._run_subprocess(deploy_cmd)
        return cmd_stdout

    @staticmethod
    def _run_subprocess(shell_cmd):
        result = subprocess.run(shell_cmd, stdout=subprocess.PIPE, encoding="utf8", check=True)
        return result.stdout

    @staticmethod
    def prefix_cmd_with_tiller_run(helm_cmd):
        HELM_TILLER_PREFIX = "helm tiller run -- "
        deploy_cmd = (HELM_TILLER_PREFIX + helm_cmd).split()
        return deploy_cmd

@pytest.fixture(scope="session")
def tango_base_release():
    # setup
    chart_name = "tango-base"
    use_tiller_plugin = True
    helm_test_adaptor = HelmTestAdaptor(chart_name, use_tiller_plugin)
    release_name = helm_test_adaptor.deploy_chart()

    # yield fixture
    Release = collections.namedtuple('Release', ['name', 'chart'])
    yield Release(release_name, chart_name)

    # teardown
    helm_test_adaptor.undeploy_chart(release_name)


@pytest.mark.no_deploy()
def test_databaseds_resource_definition_should_have_TANGO_HOST_set_to_its_own_hostname():
    a_release_name = 'any-release'
    helm_templated_defs =  HelmTestAdaptor('tango-base', False).render_template(a_release_name, 'databaseds.yaml')
    k8s_resources = _parse_yaml_resources(helm_templated_defs)
    env_vars = _env_vars_from(k8s_resources)

    expected_env_var = {
        'name': 'TANGO_HOST',
        'value': "databaseds-tango-base-{}:10000".format(a_release_name)
    }

    assert expected_env_var in env_vars

@pytest.mark.chart_deploy()
def test_tangodb_pod_should_have_mysql_server_running(tango_base_release):
        pod_name = "tangodb-{}-{}-0".format(tango_base_release.chart, tango_base_release.name)
        host = _connect_to_pod(pod_name)
        mysqld_proc = host.process.get(command="mysqld")
        assert mysqld_proc is not None


def _connect_to_pod(pod_name, namespace="ci"):
    host = testinfra.get_host("kubectl://{}?namespace={}".format(pod_name, namespace))
    return host


def _env_vars_from(databaseds_statefulset):
    databaseds_statefulset = [r for r in databaseds_statefulset if r['kind'] == 'StatefulSet'].pop()
    env_vars = databaseds_statefulset['spec']['template']['spec']['containers'][0]['env']
    return env_vars


def _parse_yaml_resources(yaml_string):
    template_objects = yaml.safe_load_all(StringIO(yaml_string))
    resource_defs = [t for t in template_objects if t is not None]
    return resource_defs
