import pytest
import os
import subprocess

from elasticsearch import Elasticsearch


@pytest.fixture(scope="session")
def helm_release():
    assert os.environ.get('HELM_RELEASE')
    return os.environ.get('HELM_RELEASE').strip().replace('-', '_').upper()

def test_fluentd_ingests_pod_stdout_into_elastic(helm_release):
    # arrange/ test setup
    log_messages = [
        "1|2019-12-31T23:42.526Z|INFO||testpackage.testmodule.TestDevice.test_fn|test.py#1|demo:yes| Regular information should be logged like this FYI",
        "1|2019-12-31T23:45.328Z|DEBUG||testpackage.testmodule.TestDevice.test_fn|test.py#150|demo:yes| x = 67, y = 24",
        "1|2019-12-31T23:49.543Z|WARNING||testpackage.testmodule.TestDevice.test_fn|test.py#16|demo:yes| z is unspecified, defaulting to 0!",
        "1|2019-12-31T23:50.124Z|ERROR||testpackage.testmodule.TestDevice.test_fn|test.py#165|demo:yes| Could not connect to database!",
        "1|2019-12-31T23:51.036Z|CRITICAL||testpackage.testmodule.TestDevice.test_fn|test.py#16|demo:yes| Invalid operation. Cannot continue."
    ]

    
    # act / initiate action under test
    _ = [subprocess.Popen(['echo "{}"'.format(msg)], shell=True) for msg in log_messages]

    # assert expected behaviour:
    # connect to elastic and search for messages
    elastic_host = os.environ.get('ELASTIC_LOGGING_{}_SERVICE_HOST'.format(helm_release))
    elastic_port = os.environ.get('ELASTIC_LOGGING_{}_SERVICE_PORT'.format(helm_release))

    host_details = {
        'host': elastic_host, 
        'port': elastic_port
    }                                                                                              
    es = Elasticsearch([host_details])

    query_body = { 
      "query": { 
          "match": { 
              "tags": "demo:yes" 
          } 
      } 
    }

    result = es.search( 
        index="logstash*", 
        body=query_body 
    )

    assert len(result.get('hits').get('hits')) > 0


def test_logstash_ingests_rsyslog_messages_into_elastic():
    # TODO write this test
    pass

