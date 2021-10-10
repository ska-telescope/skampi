import pytest

from resources.test_support.util import parse_yaml_str


@pytest.mark.no_deploy
def test_cm_service_definition_should_have_TANGO_HOST_set_to_databaseds_host(helm_adaptor):
    chart = 'archiver'
    a_release_name = 'any-release'
    helm_templated_defs = helm_adaptor.template(chart, a_release_name, 'cm_service.yaml')
    k8s_resources = parse_yaml_str(helm_templated_defs)

    cm_service_statefulset = [r for r in k8s_resources if r['kind'] == 'StatefulSet'].pop()
    env_vars = cm_service_statefulset['spec']['template']['spec']['containers'][0]['env']

    expected_env_var = {
        'name': 'TANGO_HOST',
        'value': "databaseds-tango-base-{}:10000".format(a_release_name)
    }

    assert expected_env_var in env_vars
