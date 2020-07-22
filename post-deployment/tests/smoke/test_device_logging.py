from resources.test_support.log_helping import DeviceLogging,DeviceLoggingImplWithDBDirect
import logging
import json
import pytest
from assertpy import assert_that
from time import sleep
import re
from datetime import datetime,date,timedelta
import mock
import os
import csv
from mock import MagicMock
from tango import EventData,DeviceAttribute
from elasticsearch import Elasticsearch

VAR = os.environ.get('USE_LOCAL_ELASTIC')
if (VAR == "True"):
    local_elastic_disabled = False
else:
    local_elastic_disabled = True

###to be  moved
from elasticsearch_dsl import Search,Q

@pytest.mark.devlogging

@mock.patch('resources.test_support.log_helping.TraceHelper')
def test_device_logging(mock_tracer_helper):
    # given
    mock_tracer_helper_instance = mock_tracer_helper.return_value
    mock_event = MagicMock(spec=EventData)
    mock_tracer_helper_instance.get_messages.return_value = [mock_event]
    d = DeviceLogging()
    d.update_traces(['sys/tg_test/1'])
    d.start_tracing()
    d.wait_until_message_received("DataGenerator::generating data", 20)
    d.stop_tracing()
    dict_messages = d.get_messages_as_list_dict()
    assert_that(dict_messages[0]['message'].id).is_equal_to(mock_event.attr_value.value.id)



@pytest.mark.devlogging
@mock.patch('resources.test_support.log_helping.TraceHelper')
def test_logging_on_test_device_as_string(mock_tracer_helper):
    mock_tracer_helper_instance = mock_tracer_helper.return_value
    mock_event = MagicMock(spec=EventData)
    mock_tracer_helper_instance.get_messages.return_value = [mock_event]
    d = DeviceLogging()
    d.update_traces(['sys/tg_test/1'])
    d.start_tracing()
    d.wait_until_message_received("DataGenerator::generating data", 20)
    printeable_messages = d.get_printable_messages()
    assert_that(printeable_messages).is_instance_of(str)

@pytest.mark.devlogging
def test_throw_error_():
    with pytest.raises(Exception):
        DeviceLogging("wrong implementation")

class MockObj():

    def __init__(self,the_dict):
        for key in the_dict.keys():
            setattr(self, key, the_dict[key])


def mock_hits():
    mock_hit = MockObj({
    'kubernetes': MockObj(
        {'container_name':'container_name',
        'pod_name':'pod_name' }),
    'ska_log_message': 'ska_log_message',
    'ska_log_timestamp' : 'ska_log_timestamp',
    'container' : 'container',
    })
    return [mock_hit,mock_hit]

def fake_an_es_search(mock_search):
    mock_search_instance = mock_search.return_value
    mock_search_instance.query.return_value = mock_search_instance
    mock_search_instance.sort.return_value = mock_search_instance
    mock_search_instance.source.return_value = mock_search_instance
    # mock hits is two messages that should result from the query
    mock_search_instance.scan.return_value = mock_hits()
    return mock_search_instance

def fake_device_mapping(mock_device_to_container):
    mock_device_to_container.__getitem__.return_value = 'container_name'
    return mock_device_to_container


@mock.patch('resources.test_support.log_helping.device_to_container')
@mock.patch('resources.test_support.log_helping.Elasticsearch')
@mock.patch('resources.test_support.log_helping.Search')
@pytest.mark.devlogging
#@pytest.mark.xfail
def test_log_single_device_from_elastic(mock_search,elastic_mock,mock_device_to_container):
    # given
    fake_an_es_search(mock_search)
    fake_device_mapping(mock_device_to_container)
    d = DeviceLoggingImplWithDBDirect(elastic_mock.return_value)
    d.update_devices_to_be_logged("sdp-processing-controller")
    # when
    d.start_tracing()
    d.stop_tracing()             
    # then                                                             
    res = d.get_messages_as_list_dict()
    assert_that(res[0]['device']).is_equal_to('sdp-processing-controller')
    assert_that(res[1]['device']).is_equal_to('sdp-processing-controller')

@pytest.mark.devlogging
@mock.patch('resources.test_support.log_helping.device_to_container')
@mock.patch('resources.test_support.log_helping.Elasticsearch')
@mock.patch('resources.test_support.log_helping.Search')
def test_log_multiple_devices_from_elastic(mock_search,elastic_mock,mock_device_to_container):
    # given
    fake_an_es_search(mock_search)
    # this will result in the same device mapping to container name 
    fake_device_mapping(mock_device_to_container)
    d = DeviceLoggingImplWithDBDirect(elastic_mock.return_value)
    d.update_devices_to_be_logged(["sdp-processing-controller","helm-deploy"])
    d.start_tracing() 
    d.stop_tracing()                                                                            
    res = d.get_messages_as_list_dict()
    assert_that(res[0]['device']).is_equal_to('sdp-processing-controller/helm-deploy')
    assert_that(res[1]['device']).is_equal_to('sdp-processing-controller/helm-deploy')

@pytest.fixture()
def print_to_file_fixture():
    fixture = {}
    dict_results = []
    for n in range(10):
        dict_results.append({
            "ska_log_message" : "ska_log_message{}".format(n),
            "ska_log_timestamp" : "ska_log_timestamp{}".format(n),
            "container" : "ska_log_timestamp{}".format(n),
            "pod" : "pod{}".format(n) ,
            "device" : "device{}".format(n)
        })
    fixture['mock_results'] = dict_results
    filename_csv = 'temp.csv'
    filename_json = 'temp.json'
    fixture['filename_csv'] = filename_csv
    fixture['filename_json'] = filename_json
    yield fixture
    if os.path.isfile('build/{}'.format(filename_csv)):
            os.remove('build/{}'.format(filename_csv))
    if os.path.isfile('build/{}'.format(filename_json)):
            os.remove('build/{}'.format(filename_json))

@pytest.fixture()
def device_logging_fixture():
    fixture = {}
    filename_csv = 'temp.csv'
    filename_json = 'temp.json'
    fixture['filename_csv'] = filename_csv
    fixture['filename_json'] = filename_json
    dict_results = []
    for n in range(10):
        dict_results.append({
            "ska_log_message" : "ska_log_message{}".format(n),
            "ska_log_timestamp" : "ska_log_timestamp{}".format(n),
            "container" : "ska_log_timestamp{}".format(n),
            "pod" : "pod{}".format(n) ,
            "device" : "device{}".format(n)
        })
    get_messages_as_list_dict_mock1 = MagicMock('resources.test_support.helpers.DeviceLoggingImplWithDBDirect.get_messages_as_list_dict')
    get_messages_as_list_dict_mock2 = MagicMock('resources.test_support.helpers.DeviceLoggingImplWithDBDirect.get_messages_as_list_dict')
    get_messages_as_list_dict_mock1.return_value = dict_results
    get_messages_as_list_dict_mock2.return_value = []
    elastic_mock = MagicMock(Elasticsearch)
    d1 = DeviceLoggingImplWithDBDirect(elastic_mock.return_value)
    d2 = DeviceLoggingImplWithDBDirect(elastic_mock.return_value)
    d1.get_messages_as_list_dict = get_messages_as_list_dict_mock1
    d2.get_messages_as_list_dict = get_messages_as_list_dict_mock2
    fixture['mocked_device_logging_with_dummy_data'] = d1
    fixture['mocked_device_logging_with_empty_data'] = d2
    fixture['dummy_data'] = dict_results
    yield fixture
    ##tear down
    if os.path.isfile('build/{}'.format(filename_csv)):
        os.remove('build/{}'.format(filename_csv))
    if os.path.isfile('build/{}'.format(filename_json)):
        os.remove('build/{}'.format(filename_json))

@pytest.mark.devlogging
def test_print_to_csv_file(device_logging_fixture):
    #given
    d = device_logging_fixture['mocked_device_logging_with_dummy_data']
    filename = device_logging_fixture['filename_csv']
    dummy_data = device_logging_fixture['dummy_data']
    #when
    d.print_log_to_file(filename,style='csv')
    #then
    with open('build/{}'.format(filename), 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        results = []
        for row in reader:
            results.append(row)
    assert_that(results).is_equal_to(dummy_data)

@pytest.mark.devlogging
def test_print_to_json_file(device_logging_fixture):
    #given
    d = device_logging_fixture['mocked_device_logging_with_dummy_data']
    filename = device_logging_fixture['filename_json']
    dummy_data = device_logging_fixture['dummy_data']
    #when
    d.print_log_to_file(filename,style='dict')
    #then
    with open('build/{}'.format(filename), 'r') as file:
        results = json.loads(file.read())
    assert_that(results).is_equal_to(dummy_data)

@pytest.mark.devlogging
def test_print_json_empty_file(device_logging_fixture):
    #given
    d = device_logging_fixture['mocked_device_logging_with_empty_data']
    filename = device_logging_fixture['filename_json']
    #when
    d.print_log_to_file(filename,style='dict')
    #then
    with open('build/{}'.format(filename), 'r') as file:
        results = json.loads(file.read())
    assert_that(results).is_equal_to("no data logged")

@pytest.mark.devlogging
def test_print_csv_empty_file(device_logging_fixture):
    #given
    d = device_logging_fixture['mocked_device_logging_with_empty_data']
    filename = device_logging_fixture['filename_csv']
    #when
    d.print_log_to_file(filename,style='csv')
    #then
    with open('build/{}'.format(filename), 'r') as file:
        results = json.loads(file.read())
    assert_that(results).is_equal_to("no data logged")

