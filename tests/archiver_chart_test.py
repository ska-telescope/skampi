import pytest

from tests.testsupport.util import parse_yaml_str


@pytest.mark.no_deploy
def test_archiver_pod_definition_should_have_TANGO_HOST_set_to_databaseds_host(helm_adaptor):
    chart = 'archiver'
    a_release_name = 'any-release'
    helm_templated_defs = helm_adaptor.template(chart, a_release_name, 'archiver.yaml')
    k8s_resources = parse_yaml_str(helm_templated_defs)

    archiver_pod = [r for r in k8s_resources if r['kind'] == 'Pod'].pop()
    pod_containers = [container for container in archiver_pod['spec']['containers']]

    expected_env_var = {
        'name': 'TANGO_HOST',
        'value': "databaseds-tango-base-{}:10000".format(a_release_name)
    }

    for container in pod_containers:
        assert expected_env_var in container['env']
