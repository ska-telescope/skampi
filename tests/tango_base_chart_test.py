import subprocess
import collections

import pytest
import testinfra
import yaml

from io import StringIO


@pytest.fixture(scope="session")
def tango_base_release():
    # setup
    chart_name = "tango-base"
    helm_release = _helm_install(chart_name)

    # yield fixture
    Release = collections.namedtuple('Release', ['name', 'chart'])
    yield Release(helm_release, chart_name)

    # teardown
    _helm_delete(helm_release, 'helm tiller run -- ')


@pytest.mark.no_deploy()
def test_databaseds_resource_definition_should_have_TANGO_HOST_set_to_its_own_hostname():
    a_release_name = 'any-release'
    helm_templated_defs = _helm_template('tango-base', a_release_name, 'databaseds.yaml')
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


def _helm_delete(helm_release, helm_cmd_prefix):
    helm_delete_cmd = "helm delete {} --purge".format(helm_release)
    del_result = subprocess.run((helm_cmd_prefix + helm_delete_cmd).split(), stdout=subprocess.PIPE,
                                encoding="utf8", check=True)


def _helm_install(chart="tango-base"):
    helm_install_cmd = "helm install charts/{} --namespace ci --wait".format(chart)
    helm_tiller_prefix = "helm tiller run -- "
    wrapped_cmd = (helm_tiller_prefix + helm_install_cmd).split()
    result = subprocess.run(wrapped_cmd, stdout=subprocess.PIPE, encoding="utf8", check=True)
    release_name_line = ''.join(l for l in result.stdout.split('\n') if l.startswith('NAME:'))
    release_name = release_name_line.split().pop()
    return release_name


def _env_vars_from(databaseds_statefulset):
    databaseds_statefulset = [r for r in databaseds_statefulset if r['kind'] == 'StatefulSet'].pop()
    env_vars = databaseds_statefulset['spec']['template']['spec']['containers'][0]['env']
    return env_vars


def _helm_template(chart, release_name, template):
    helm_template_cmd = "helm template --name {} -x templates/{} charts/{}".format(release_name, template,
                                                                                   chart)
    result = subprocess.run(helm_template_cmd.split(), stdout=subprocess.PIPE, encoding="utf8")
    return result.stdout

def _parse_yaml_resources(yaml_string):
    template_objects = yaml.safe_load_all(StringIO(yaml_string))
    resource_defs = [t for t in template_objects if t is not None]
    return resource_defs
