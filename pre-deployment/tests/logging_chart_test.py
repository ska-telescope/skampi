import json
import logging

import pytest

from resources.test_support.extras import EchoServer
from resources.test_support.helm import HelmChart, ChartDeployment
from resources.test_support.util import wait_until


@pytest.fixture(scope="class")
def logging_chart(request, helm_adaptor):
    chart_values = {
        'demo_mode.enabled': 'true'
    }
    request.cls.chart = HelmChart('logging', helm_adaptor, initial_chart_values=chart_values)


@pytest.fixture(scope="class")
def throttled_logging_chart(request, helm_adaptor):
    throttle_settings = {
        'fluentd.logging_rate_throttle.enabled': 'true',
        'fluentd.logging_rate_throttle.group_bucket_period_s': '1',
        'fluentd.logging_rate_throttle.group_bucket_limit': '20',
        'fluentd.logging_rate_throttle.group_reset_rate_s': '5'
    }
    throttle_settings['demo_mode.enabled'] = 'true'
    request.cls.chart = HelmChart('logging', helm_adaptor,
                                  initial_chart_values=throttle_settings)


@pytest.fixture(scope="class")
def logging_chart_deployment(helm_adaptor, k8s_api):
    logging.info("+++ Deploying logging chart.")
    throttle_settings = {'fluentd.logging_rate_throttle.enabled': 'false'}
    chart_deployment = ChartDeployment('logging', helm_adaptor, k8s_api,
                                       set_flag_values=throttle_settings)
    yield chart_deployment
    logging.info("+++ Deleting logging chart release.")
    chart_deployment.delete()


@pytest.fixture(scope="function")
def echoserver(test_namespace):
    logging.info("+++ Deploying echoserver pod.")
    echoserver = EchoServer(test_namespace)
    yield echoserver
    logging.info("+++ Deleting echoserver pod.")
    echoserver.delete()


@pytest.fixture(scope="class")
def logging_chart_throttled_deployment(helm_adaptor, k8s_api):
    logging.info("+++ Deploying throttled logging chart.")

    throttle_settings = {
        'fluentd.logging_rate_throttle.enabled': 'true',
        'fluentd.logging_rate_throttle.group_bucket_period_s': '1',
        'fluentd.logging_rate_throttle.group_bucket_limit': '20',
        'fluentd.logging_rate_throttle.group_reset_rate_s': '5'
    }

    chart_deployment = ChartDeployment('logging', helm_adaptor, k8s_api,
                                       set_flag_values=throttle_settings)
    yield chart_deployment
    logging.info("+++ Deleting throttled logging chart release.")
    chart_deployment.delete()


class SearchElasticMixin:

    def query_elasticsearch_for_log(self, chart_deployment, log_msg):
        """Execute a elastic search query"""

        elastic_pod_name = chart_deployment.search_pod_name('elastic-logging')[0]

        query_body = {
            "query": {
                "query_string": {
                    "query": log_msg,
                    "fields": ["log", "MESSAGE"]
                }
            }
        }

        command_str = ("curl -s -X GET http://0.0.0.0:9200/logstash-*/_search "
                       "-H 'Content-Type: application/json' "
                       "-H 'Accept: application/json' "
                       "-d '{}' ").format(json.dumps(query_body))

        resp = chart_deployment.pod_exec_bash(elastic_pod_name, command_str)
        logging.info("Elastic search, pod_name: %s, command: %s, response: %s",
                     elastic_pod_name, command_str, resp)
        return json.loads(resp)


@pytest.mark.no_deploy
@pytest.mark.usefixtures("logging_chart")
class TestLoggingChartTemplates:

    def test_throttling_is_disabled(self):
        resources = self.chart.templates['fluentd-config-map.yaml'].as_collection()
        ska_conf = list(filter(lambda x: 'ska.conf'in x['data'], resources))[0]

        assert 'group_bucket_period_s 1' not in ska_conf['data']['ska.conf']
        assert 'group_bucket_limit 20' not in ska_conf['data']['ska.conf']
        assert 'group_reset_rate_s 5' not in ska_conf['data']['ska.conf']

    def test_elastic_service_is_exposed_on_port_9200_for_all_k8s_nodes(self):
        elastic_resources = self.chart.templates['elastic.yaml'].as_collection()
        elastic_svc = list(filter(lambda x: x['kind'] == 'Service', elastic_resources))[0]

        expected_portmapping = {
            "port": 9200,
            "targetPort": 9200
        }

        assert elastic_svc['spec']['type'] == 'NodePort'
        assert expected_portmapping in elastic_svc['spec']['ports']

    def test_fluentd_is_authorised_to_read_pods_and_namespaces_cluster_wide(self):
        resources = self.chart.templates['fluentd-rbac.yaml'].as_collection()
        serviceaccount = list(filter(lambda x: x['kind'] == 'ServiceAccount', resources))[0]
        clusterrole = list(filter(lambda x: x['kind'] == 'ClusterRole', resources))[0]
        clusterrolebinding = list(filter(lambda x: x['kind'] == 'ClusterRoleBinding', resources))[0]

        daemonset = self.chart.templates['fluentd-daemonset.yaml'].as_collection().pop()
        serviceaccount_name = serviceaccount['metadata']['name']

        expected_auth_rule = {
            "apiGroups": [""],
            "resources": ["pods", "namespaces"],
            "verbs": ["get", "list", "watch"]
        }

        assert expected_auth_rule in clusterrole['rules']
        assert serviceaccount_name in [s['name'] for s in clusterrolebinding['subjects']]
        assert daemonset['spec']['template']['spec']['serviceAccountName'] == serviceaccount_name

    def test_fluentd_is_configured_to_integrate_with_elastic_via_incluster_hostname(self):
        resources = self.chart.templates['elastic.yaml'].as_collection()
        elastic_deployment = list(filter(lambda x: x['kind'] == 'Deployment', resources))[0]
        elastic_svc = list(filter(lambda x: x['kind'] == 'Service', resources))[0]

        fluentd_daemonset = self.chart.templates['fluentd-daemonset.yaml'].as_collection().pop()

        expected_env_vars = [
            {"FLUENT_ELASTICSEARCH_HOST": elastic_deployment['metadata']['name']},
            {"FLUENT_ELASTICSEARCH_PORT": str(elastic_svc['spec']['ports'].pop()['port'])},
        ]

        fluentd_container = fluentd_daemonset['spec']['template']['spec']['containers'][0]
        env_vars = [{v['name']: v['value']} for v in fluentd_container['env']]

        for env_var in expected_env_vars:
            assert env_var in env_vars

    def test_elastic_ilm_chart_yaml(self):
        """Check that the values.yaml is applied as expected"""
        template = self.chart.templates['elastic-config-map.yaml']
        elastic_cm = template.as_collection()[0]
        assert 'ska_ilm_policy.json' in elastic_cm['data']
        ska_ilm_policy = json.loads(elastic_cm['data']['ska_ilm_policy.json'])
        ska_ilm_policy_phases = ska_ilm_policy['policy']['phases']
        assert ska_ilm_policy_phases['hot']['actions']['rollover']['max_size'] == '1gb'
        assert ska_ilm_policy_phases['hot']['actions']['rollover']['max_age'] == '1d'
        assert ska_ilm_policy_phases['delete']['min_age'] == '1d'


@pytest.mark.no_deploy
@pytest.mark.usefixtures("throttled_logging_chart")
class TestLoggingChartThrottledTemplates:
    def test_throttle_settings_applied(self):
        resources = self.chart.templates['fluentd-config-map.yaml'].as_collection()
        ska_conf = list(filter(lambda x: 'ska.conf'in x['data'], resources))[0]

        assert 'group_bucket_period_s 1' in ska_conf['data']['ska.conf']
        assert 'group_bucket_limit 20' in ska_conf['data']['ska.conf']
        assert 'group_reset_rate_s 5' in ska_conf['data']['ska.conf']


@pytest.mark.chart_deploy
@pytest.mark.usefixtures("logging_chart_deployment")
@pytest.mark.quarantine
class TestLoggingDeployment(SearchElasticMixin):

    @pytest.mark.usefixtures("echoserver")
    def test_fluentd_ingests_logs_from_pod_stdout_into_elasticsearch(self,
                                                                     logging_chart_deployment,
                                                                     echoserver,
                                                                     test_namespace):
        expected_log = "simple were so well compounded"
        echoserver.print_to_stdout(expected_log)

        def _wait_for_elastic_hits():
            result = self.query_elasticsearch_for_log(logging_chart_deployment, expected_log)
            return result['hits']['total']['value'] != 0

        wait_until(_wait_for_elastic_hits, retry_timeout=500)

    def test_elastic_config_applied(self, logging_chart_deployment, test_namespace):
        """ Test that the elastic config has been applied"""

        elastic_pod_name = logging_chart_deployment.search_pod_name('elastic-logging')[0]

        # ilm
        command_str = 'curl -s  -X GET http://0.0.0.0:9200/_ilm/policy/ska_ilm_policy'
        resp = logging_chart_deployment.pod_exec_bash(elastic_pod_name, command_str)
        resp = resp.replace("'", '"')
        logging.info(resp)
        resp_json = json.loads(resp)
        assert 'ska_ilm_policy' in resp_json

        # pipeline parse
        log_string = ("1|2020-01-14T08:24:54.560513Z|DEBUG|thread_id_123|"
                      "demo.stdout.logproducer|logproducer.py#1|tango-device:my/dev/name|"
                      "A log line from stdout.")
        doc = {"docs": [{"_source": {"log": log_string}}]}
        command_str = ("curl -s  -X POST http://0.0.0.0:9200/"
                       "_ingest/pipeline/ska_log_parsing_pipeline/_simulate "
                       "-H 'Content-Type: application/json' "
                       "-d '{}' ").format(json.dumps(doc))
        resp = logging_chart_deployment.pod_exec_bash(elastic_pod_name, command_str)
        resp = resp.replace("'", '"')
        logging.info(resp)
        res_json = json.loads(resp)
        source = res_json["docs"][0]['doc']['_source']
        assert source['ska_line_loc'] == "logproducer.py#1"
        assert source['ska_function'] == "demo.stdout.logproducer"
        assert source['ska_version'] == "1"
        assert source['ska_log_timestamp'] == "2020-01-14T08:24:54.560513Z"
        assert source['ska_tags'] == "tango-device:my/dev/name"
        assert source['ska_severity'] == "DEBUG"
        assert source['ska_log_message'] == "A log line from stdout."
        assert source['ska_thread_id'] == "thread_id_123"

    def test_kibana_is_up_with_correct_base_path(self, logging_chart_deployment):
        """Check that Kibana is up and base path is as expected"""
        kibana_pod_name = logging_chart_deployment.search_pod_name('kibana-deployment')[0]
        BASE_PATH = "/kibana"
        command_str = ('curl -s  -X GET '
                       'http://0.0.0.0:5601{}/api/spaces/space').format(BASE_PATH)

        resp = logging_chart_deployment.pod_exec_bash(kibana_pod_name, command_str)
        resp = resp.replace("'", '"')
        resp = resp.replace("True", "true")
        logging.info(resp)
        assert len(json.loads(resp)) > 0


@pytest.mark.chart_deploy
@pytest.mark.usefixtures("logging_chart_throttled_deployment")
@pytest.mark.quarantine
class TestThrottlingLoggingDeployment(SearchElasticMixin):

    def test_log_throttling_happens(self, logging_chart_throttled_deployment,
                                    test_namespace):
        """Check that logs are throttled per container"""
        pod_manifest = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'name': 'flood-logs',
                'namespace': test_namespace
            },
            'spec': {
                'containers': [{
                    'image': 'alpine:latest',
                    'name': 'flood-logs',
                    "args": [
                        "/bin/sh",
                        "-c",
                        "while true; do echo \"Flood the logs\" | tee /dev/stderr; sleep 0.25; done"
                    ]
                }],
                'restartPolicy': 'Never'
            }
        }
        logging_chart_throttled_deployment.launch_pod_manifest(pod_manifest)

        def _wait_for_elastic_hits():
            result = self.query_elasticsearch_for_log(logging_chart_throttled_deployment,
                                                      '(rate exceeded group_key) AND (period_s=1 limit=20 rate_limit_s=20 reset_rate_s=5)')
            return result['hits']['total']['value'] != 0

        wait_until(_wait_for_elastic_hits, retry_timeout=500)
