from io import StringIO

import pytest
import testinfra
import yaml

from tests.testsupport.helm import ChartDeployment


@pytest.fixture(scope="module")
def tango_base_release(helm_adaptor):
    tango_base_release = ChartDeployment("tango-base", helm_adaptor) # setup
    yield tango_base_release # yield fixture
    tango_base_release.delete() # teardown


@pytest.mark.no_deploy()
def test_databaseds_resource_definition_should_have_TANGO_HOST_set_to_its_own_hostname(helm_adaptor):
    chart = 'tango-base'
    a_release_name = 'any-release'
    helm_templated_defs = helm_adaptor.template(chart, a_release_name, 'databaseds.yaml')
    k8s_resources = _parse_yaml_resources(helm_templated_defs)
    env_vars = _env_vars_from(k8s_resources)

    expected_env_var = {
        'name': 'TANGO_HOST',
        'value': "databaseds-tango-base-{}:10000".format(a_release_name)
    }

    assert expected_env_var in env_vars


@pytest.mark.chart_deploy()
def test_tangodb_pod_should_have_mysql_server_running(tango_base_release, test_namespace):
        pod_name = "tangodb-{}-{}-0".format(tango_base_release.chart_name, tango_base_release.release_name)
        host = _connect_to_pod(pod_name, test_namespace)
        mysqld_proc = host.process.get(command="mysqld")
        assert mysqld_proc is not None


def _connect_to_pod(pod_name, namespace):
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
