import os
import pytest
import logging

from elasticsearch import Elasticsearch


def test_noop():
    logging.info('Helm chart tests are running!')
    assert True


def test_fluentd_ingests_pod_stdout_into_elastic(run_context):
    # arrange/ test setup

    NAMESPACE = run_context.KUBE_NAMESPACE
    print("Namespace:", NAMESPACE)
    RELEASE = run_context.HELM_RELEASE
    print("Namespace:", RELEASE.upper())

    # connect to elastic and search for messages
    elastic_host = os.environ.get('ELASTIC_LOGGING_{}_PORT_9200_TCP_ADDR'.format(RELEASE.upper()))
    elastic_port = os.environ.get('ELASTIC_LOGGING_{}_SERVICE_PORT'.format(RELEASE.upper()))
    es = Elasticsearch(["{}:{}".format(elastic_host, elastic_port)],
                       use_ssl=False,
                       verify_certs=False,
                       ssl_show_warn=False)

    print("es :", es)
    search_tmc = {
        "query": {
            "match": {
                "kubernetes.pod_name.keyword": {
                    "query": "tmcprototype-tmc-proto-test"
                }
            }
        }
    }

    result = es.search(
        index='logstash*',
        body=search_tmc
    )
    print("Result :", result['hits']['total']['value'])
    no_of_hits = result['hits']['total']['value']
    assert no_of_hits > 0
