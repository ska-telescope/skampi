import os

from elasticsearch import Elasticsearch


KUBE_NAMESPACE = 'SARAO'

def test_fluentd_ingests_pod_stdout_into_elastic():
    # arrange/ test setup
    log_messages = [
        "1|2019-12-31T23:42.526Z||testpackage.testmodule.TestDevice.test_fn|test.py#1    |INFO    |demo:yes| Regular information should be logged like this FYI",
        "1|2019-12-31T23:45.328Z||testpackage.testmodule.TestDevice.test_fn|test.py#150  |DEBUG   |demo:yes| x = 67, y = 24",
        "1|2019-12-31T23:49.543Z||testpackage.testmodule.TestDevice.test_fn|test.py#16   |WARNING |demo:yes| z is unspecified, defaulting to 0!",
        "1|2019-12-31T23:50.124Z||testpackage.testmodule.TestDevice.test_fn|test.py#165  |ERROR   |demo:yes| Could not connect to database!",
        "1|2019-12-31T23:51.036Z||testpackage.testmodule.TestDevice.test_fn|test.py#16   |CRITICAL|demo:yes| Invalid operation. Cannot continue."
    ]

    
    # act / initiate action under test
    _ = [print(msg) for msg in log_messages]

    # assert expected behaviour:
    # connect to elastic and search for messages
    elastic_host = os.environ.get('ELASTIC_LOGGING_{}_PORT_9200_TCP_ADDR'.format(KUBE_NAMESPACE))
    elastic_port = os.environ.get('ELASTIC_LOGGING_{}_SERVICE_PORT'.format(KUBE_NAMESPACE))

    host_details = {
        'host': elastic_host, 
        'port': elastic_port, 
        'url_prefix': 'elasticsearch'}                                                                                              

    es = Elasticsearch([host_details])

    query_body = { 
      "query": { 
          "match": { 
              "tags": "demo:yes" 
          } 
      } 
    }

    result = es.search( 
        index="log*", 
        body=query_body 
    )

    assert len(result.get('hits')) > 0


def test_logstash_ingests_rsyslog_messages_into_elastic():
    # TODO write this test
    pass

