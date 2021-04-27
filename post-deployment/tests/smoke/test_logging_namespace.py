import pytest
import socket
import logging
from elasticsearch import Elasticsearch
from resources.log_consumer.tracer_helper import TraceHelper

@pytest.mark.logging
@pytest.mark.skamid
@pytest.mark.skip(reason="ELK moved")
def test_logging_namespace(run_context):
    """Test that we only get logs from our namespace"""

    ES_HOST = "elastic-logging-{}".format(run_context.HELM_RELEASE)
    ES_PORT = "9200"
    NAMESPACE = run_context.KUBE_NAMESPACE
    INDEX_MATCH = "lo*-*"
    local = True
    tracer = TraceHelper()
    if tracer.check_port(ES_HOST, ES_PORT) != 0:
        ES_HOST = "192.168.93.94"
        ES_PORT = "9200"
        NAMESPACE = run_context.KUBE_NAMESPACE
        INDEX_MATCH = "fi*-*"
        local = False

    es = Elasticsearch(["{}:{}".format(ES_HOST, ES_PORT)],
                       use_ssl=False,
                       verify_certs=False,
                       ssl_show_warn=False)

    indexes = es.indices.get(INDEX_MATCH)
    
    assert indexes, "No indexes found that match [{}]".format(INDEX_MATCH)
    last_index = sorted(indexes,
                        key=lambda i: indexes[i]['settings']['index']['creation_date'],
                        reverse=True)[0]

    label_namespace = "container.labels.io_kubernetes_pod_namespace"

    if(local):
        label_namespace = "kubernetes_namespace"

    search_namespace = {
        "query": {
            "match": {
                label_namespace: {
                    "query": NAMESPACE
                }
            }
        }
    }

    search_not_namespace = {
        "query": {
            "bool": {
                "must_not": [
                    {
                        "term": {
                            label_namespace: NAMESPACE
                        }
                    }
                ],
                "must": [
                    {
                        "exists": {
                            "field": label_namespace
                        }
                    }
                ]
            }
        }
    }

    res = es.search(index=last_index, body=search_namespace)
    assert res['hits']['total']['value'], ("Found no matches for namespace [{}] using"
                                           " index [{}]".format(NAMESPACE, last_index))
    if(local):
        res = es.search(index=last_index, body=search_not_namespace)
        assert not res['hits']['total']['value'], "Found matches on other namespaces"
