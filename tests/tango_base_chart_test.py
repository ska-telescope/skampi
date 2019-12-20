import subprocess
import yaml

from io import StringIO


def test_databaseds_resource_definition_should_have_TANGO_HOST_set_to_its_own_hostname():
    release_name = 'any-release'

    helm_template_cmd = "helm template --name {} -x templates/{} charts/{}".format(release_name, "databaseds.yaml", "tango-base")
    result = subprocess.run(helm_template_cmd.split(), stdout=subprocess.PIPE, encoding="utf8")

    stream = StringIO(result.stdout)
    rendered_templates = yaml.safe_load_all(stream)
    resource_defs = [t for t in rendered_templates if t is not None]

    databaseds_statefulset = [r for r in resource_defs if r['kind'] == 'StatefulSet'].pop()
    env_vars = databaseds_statefulset['spec']['template']['spec']['containers'][0]['env']

    expected_env_var = {
        'name': 'TANGO_HOST',
        'value': "databaseds-tango-base-{}:10000".format(release_name)
    }

    assert expected_env_var in env_vars

