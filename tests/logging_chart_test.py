import logging
import subprocess
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
    def test_pvc_reclaim_policy_is_set_to_Delete(self):
        resources = parse_yaml_str(self.chart.templates['elastic-pv.yaml'])

        assert resources[0]['spec']['persistentVolumeReclaimPolicy'] == 'Delete'

    def test_elastic_service_is_exposed_on_port_9200_for_all_k8s_nodes(self):
        elastic_svc = parse_yaml_str(self.chart.templates['elastic.yaml'])[1]

        expected_portmapping = {
            "port": 9200,
            "targetPort": 9200
        }

        assert elastic_svc['spec']['type'] == 'NodePort'
        assert expected_portmapping in elastic_svc['spec']['ports']

    def test_elastic_curator_set_to_run_once_every_hour(self):
        curator_job = parse_yaml_str(self.chart.templates['elastic_curator.yaml']).pop()

        assert curator_job['spec']['schedule'] == '0 1 * * *'

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

    def test_elastic_pvc_has_label_selector_to_match_pv_app_and_release(self):
        elastic_pv, elastic_pvc = parse_yaml_str(self.chart.templates['elastic-pv.yaml'])
        elastic_pv_app_label = elastic_pv['metadata']['labels']['app']
        elastic_pv_release_label = elastic_pv['metadata']['labels']['release']

        expected_matchlabels = {
            "app": elastic_pv_app_label,
            "release": elastic_pv_release_label
        }

        assert elastic_pvc['spec']['selector']['matchLabels'] == expected_matchlabels


@pytest.fixture(scope="module")
def logging_chart_deployment(helm_adaptor, k8s_api):
    logging.info("+++ Deploying logging chart.")
    chart_deployment = ChartDeployment('logging', helm_adaptor, k8s_api)
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


@pytest.mark.quarantine
@pytest.mark.chart_deploy
@pytest.mark.usefixtures("elastic_svc_proxy")
def test_fluentd_ingests_logs_from_pod_stdout_into_elasticsearch(logging_chart_deployment, echoserver, test_namespace):
    # act:
    expected_log = "simple were so well compounded"
    echoserver.print_to_stdout(expected_log)
    # TODO solve _wait_until_fluentd_ingests_echoserver_logs for journald-fluentd integration
    sleep(80) # not ideal because this varies with load
    # fluentd_daemonset_name = "daemonset/fluentd-logging-{}".format(logging_chart_deployment.release_name)
    # _wait_until_fluentd_ingests_echoserver_logs(
    #     fluentd_daemonset_name, datetime.now(), test_namespace)

    # assert:
    result = _query_elasticsearch_for_log(expected_log)
    assert len(result['hits']['hits']) > 0


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
