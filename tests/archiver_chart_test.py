from io import StringIO

import pytest
import yaml

from tests.testsupport.helm import HelmTestAdaptor


@pytest.mark.no_deploy
def test_archiver_pod_definition_should_have_TANGO_HOST_set_to_databaseds_host():
    chart = 'archiver'
    a_release_name = 'any-release'
    helm_templated_defs = HelmTestAdaptor(False).template(chart, a_release_name, 'archiver.yaml')
    template_objects = yaml.safe_load_all(StringIO(helm_templated_defs))
    k8s_resources = [t for t in template_objects if t is not None]

    archiver_pod = [r for r in k8s_resources if r['kind'] == 'Pod'].pop()
    pod_containers = [container for container in archiver_pod['spec']['containers']]

    expected_env_var = {
        'name': 'TANGO_HOST',
        'value': "databaseds-tango-base-{}:10000".format(a_release_name)
    }

    for container in pod_containers:
        assert expected_env_var in container['env']
