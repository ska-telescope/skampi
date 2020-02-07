import logging
import subprocess
import json
from datetime import datetime
from time import sleep

import pytest
from elasticsearch import Elasticsearch

from tests.testsupport.extras import EchoServer
from tests.testsupport.helm import HelmChart, ChartDeployment
from tests.testsupport.util import check_connection, wait_until, parse_yaml_str


@pytest.fixture(scope="class")
def logging_chart(request, helm_adaptor):
    request.cls.chart = HelmChart('logging', helm_adaptor)


@pytest.mark.no_deploy
@pytest.mark.usefixtures("logging_chart")
class TestLoggingChartTemplates:

    def test_elastic_service_is_exposed_on_port_9200_for_all_k8s_nodes(self):
        elastic_svc = parse_yaml_str(self.chart.templates['elastic.yaml'])[1]

        expected_portmapping = {
            "port": 9200,
            "targetPort": 9200
        }

        assert elastic_svc['spec']['type'] == 'NodePort'
        assert expected_portmapping in elastic_svc['spec']['ports']

    def test_fluentd_is_authorised_to_read_pods_and_namespaces_cluster_wide(self):
        serviceaccount, clusterrole, clusterrolebinding = parse_yaml_str(
            self.chart.templates['fluentd-rbac.yaml'])
        daemonset = parse_yaml_str(self.chart.templates['fluentd-daemonset.yaml']).pop()
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
        elastic_deployment, elastic_svc, _ = parse_yaml_str(self.chart.templates['elastic.yaml'])
        fluentd_daemonset = parse_yaml_str(self.chart.templates['fluentd-daemonset.yaml']).pop()

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
        elastic_cm = parse_yaml_str(template)[0]
        assert 'ska_ilm_policy.json' in elastic_cm['data']
        ska_ilm_policy = json.loads(elastic_cm['data']['ska_ilm_policy.json'])
        ska_ilm_policy_phases = ska_ilm_policy['policy']['phases']
        assert ska_ilm_policy_phases['hot']['actions']['rollover']['max_size'] == '1gb'
        assert ska_ilm_policy_phases['hot']['actions']['rollover']['max_age'] == '1d'
        assert ska_ilm_policy_phases['delete']['min_age'] == '1d'


@pytest.fixture(scope="module")
def logging_chart_deployment(helm_adaptor, k8s_api):
    logging.info("+++ Deploying logging chart.")
    chart_values = {
        "elastic.use_pv": "false"
    }

    chart_deployment = ChartDeployment('logging', helm_adaptor, k8s_api, values=chart_values)
    yield chart_deployment
    logging.info("+++ Deleting logging chart release.")
    chart_deployment.delete()


@pytest.fixture(scope="module")
def echoserver(test_namespace):
    logging.info("+++ Deploying echoserver pod.")
    echoserver = EchoServer(test_namespace)
    yield echoserver
    logging.info("+++ Deleting echoserver pod.")
    echoserver.delete()


@pytest.fixture(scope="module")
def elastic_svc_proxy(logging_chart_deployment, test_namespace):
    elastic_svc_name = _get_elastic_svc_name(logging_chart_deployment)
    proxy_proc = subprocess.Popen(
        "kubectl port-forward -n {} svc/{} 9200:9200".format(test_namespace, elastic_svc_name).split())

    def elastic_proxy_is_ready():
        return check_connection('127.0.0.1', 9200)

    wait_until(elastic_proxy_is_ready)
    yield
    proxy_proc.kill()


@pytest.mark.chart_deploy
@pytest.mark.quarantine
@pytest.mark.usefixtures("elastic_svc_proxy")
def test_fluentd_ingests_logs_from_pod_stdout_into_elasticsearch(logging_chart_deployment, echoserver, test_namespace):
    expected_log = "simple were so well compounded"
    echoserver.print_to_stdout(expected_log)

    def _wait_for_elastic_hits():
        result = _query_elasticsearch_for_log(expected_log)
        return result['hits']['total']['value'] != 0

    wait_until(_wait_for_elastic_hits, retry_timeout=500)

@pytest.mark.chart_deploy
def test_elastic_config_applied(logging_chart_deployment, test_namespace):
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


@pytest.mark.chart_deploy
def test_kibana_is_up_with_correct_base_path(logging_chart_deployment):
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


def _get_elastic_svc_name(logging_chart_deployment):
    elastic_svc_name = [svc.metadata.name for svc in logging_chart_deployment.get_services() if
                        svc.metadata.name.startswith('elastic-')].pop()
    return elastic_svc_name


def _wait_until_fluentd_ingests_echoserver_logs(fluentd_daemonset_name, start_timestamp, namespace):
    def fluentd_ingests_echoserver_logs():
        seconds_since_start = (datetime.now() - start_timestamp).total_seconds()
        cmd = "kubectl logs {} -n {} --all-containers --since={}s | grep -q echoserver".format(fluentd_daemonset_name,
                                                                                               namespace,
                                                                                               int(seconds_since_start))
        return subprocess.run(cmd, shell=True).returncode == 0

    wait_until(fluentd_ingests_echoserver_logs, retry_timeout=120)
    sleep(5)


def _query_elasticsearch_for_log(log_msg):
    es = Elasticsearch(['127.0.0.1:9200'], use_ssl=False, verify_certs=False, ssl_show_warn=False)
    query_body = {
        "query": {
            "multi_match": {
                "query": log_msg,
                "fields": ["log", "MESSAGE"]
            }
        }
    }
    result = es.search(
        index="logstash-*",
        body=query_body
    )

    logging.debug(result)
    return result
