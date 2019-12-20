import subprocess
import yaml

from io import StringIO


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
