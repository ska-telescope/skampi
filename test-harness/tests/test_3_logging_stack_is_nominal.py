import os
import pytest
import requests
import json
import pytest
import logging
import datetime

from elasticsearch import Elasticsearch
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def requests_retry_session(retries=3,
        backoff_factor=0.3, 
        status_forcelist=(500, 502, 504),
        session=None):

    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def test_kibana_should_be_accessible_via_ingress(run_context):
    HOSTNAME = "kibana-logging-{}-{}".format(run_context.KUBE_NAMESPACE,
                                             run_context.HELM_RELEASE)
    BASE_PATH = "/kibana"

    url = "http://{}:5601{}/app/kibana".format(HOSTNAME, BASE_PATH)
    res = requests_retry_session().get(url)

    assert res.status_code == 200


def test_log_parsing_into_elasticsearch(run_context):
    """Test that the pipeline is added and parses as expected
    """
    ES_HOST = "elastic-logging-{}".format(run_context.HELM_RELEASE)
    ES_PORT = "9200"

    es_test_parse_url = "http://{}:{}/_ingest/pipeline/ska_log_parsing_pipeline/_simulate"
    es_test_parse_url = es_test_parse_url.format(ES_HOST, ES_PORT)

    log_string = ("1|2020-01-14T08:24:54.560513Z|DEBUG|thread_id_123|"
                  "demo.stdout.logproducer|logproducer.py#1|tango-device:my/dev/name|"
                  "A log line from stdout.")

    res = requests.post(es_test_parse_url,
                        json={"docs": [{"_source": {"log": log_string}}]})

    assert res.status_code == 200
    assert res.json()["docs"]
    assert res.json()["docs"][0]['doc']
    source = res.json()["docs"][0]['doc']['_source']
    assert source['ska_line_loc'] == "logproducer.py#1"
    assert source['ska_function'] == "demo.stdout.logproducer"
    assert source['ska_version'] == "1"
    assert source['ska_log_timestamp'] == "2020-01-14T08:24:54.560513Z"
    assert source['ska_tags'] == "tango-device:my/dev/name"
    assert source['ska_severity'] == "DEBUG"
    assert source['ska_log_message'] == "A log line from stdout."
    assert source['ska_thread_id'] == "thread_id_123"


def test_ska_logs_into_elasticsearch(run_context):
    """Check that we can search on a SKA parsed field"""
    NAMESPACE = run_context.KUBE_NAMESPACE
    logging.info("Namespace:" + str(NAMESPACE))
    RELEASE = run_context.HELM_RELEASE
    logging.info("Namespace:" + str(RELEASE.upper()))
    time_stamp = datetime.datetime.utcnow()

    # connect to elastic and search for messages
    elastic_host = os.environ.get('ELASTIC_LOGGING_{}_PORT_9200_TCP_ADDR'.format(RELEASE.upper()))
    elastic_port = os.environ.get('ELASTIC_LOGGING_{}_SERVICE_PORT'.format(RELEASE.upper()))
    es = Elasticsearch(["{}:{}".format(elastic_host, elastic_port)],
                       use_ssl=False,
                       verify_certs=False,
                       ssl_show_warn=False)

    log_string = ("4|2020-01-14T08:24:54.560513Z|DEBUG|thread_id_123|"
                  "demo.stdout.logproducer|logproducer.py#1|tango-device:my/dev/name|")
    log_message = "A log line from stdout created at {}".format(time_stamp)

    doc = {"log": log_string + log_message,
           "kubernetes_namespace": run_context.KUBE_NAMESPACE,
           "@timestamp": time_stamp.isoformat()}

    indexes = es.indices.get("log*")
    last_index = sorted(indexes,
                        key=lambda i: indexes[i]['settings']['index']['creation_date'],
                        reverse=True)[0]

    es.index(index=last_index, body=doc)

    search_ska_log_message = {
        "query": {
            "match": {
                "ska_log_message": {
                    "query": log_message,
                    "operator": "and"
                }
            }
        }
    }

    result = es.search(
        index=last_index,
        body=search_ska_log_message
    )
    assert result['hits']['total']['value'] == 1
