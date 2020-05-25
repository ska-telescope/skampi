from resources.test_support.log_helping import DeviceLogging,DeviceLoggingImplWithDBDirect, get_log_stash_db
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

VAR = os.environ.get('USE_LOCAL_ELASTIC')
if (VAR == "True"):
    local_elastic_disabled = False
else:
    local_elastic_disabled = True

###to be  moved
from elasticsearch_dsl import Search,Q

@pytest.mark.skipif(local_elastic_disabled,reason="only enabled for dev purposes")
@pytest.mark.tracer
def test_device_logging():
    d = DeviceLogging()
    d.update_traces(['sys/tg_test/1'])
    logging.debug('starting traces for sys/tg_test/1')
    d.start_tracing()
    d.wait_until_message_received("DataGenerator::generating data", 20)
    dict_messages_before = d.get_messages_as_list_dict()
    d.stop_tracing()
    d = DeviceLogging("TracerHelper")
    d.update_traces(['sys/tg_test/1'])
    logging.debug('starting traces again for for sys/tg_test/1')
    d.start_tracing()
    sleep(3)
    dict_messages_after = d.get_messages_as_list_dict()
    d.stop_tracing()
    assert_that(dict_messages_before).is_not_equal_to(dict_messages_after)


@pytest.mark.skipif(local_elastic_disabled,reason="only enabled for dev purposes")
def test_logging_on_test_device_as_string():
    d = DeviceLogging()
    d.update_traces(['sys/tg_test/1'])
    logging.debug('starting traces for sys/tg_test/1')
    d.start_tracing()
    d.wait_until_message_received("DataGenerator::generating data", 20)
    printeable_messages = d.get_printable_messages()
    assert_that(printeable_messages).is_instance_of(str)
    assert_that(printeable_messages).contains("DataGenerator::generating data")

@pytest.mark.skipif(local_elastic_disabled,reason="only enabled for dev purposes")
def test_throw_error_():
    with pytest.raises(Exception):
        DeviceLogging("wrong implementation")

@pytest.mark.skipif(local_elastic_disabled,reason="only enabled for dev purposes")
def test_log_single_device_from_elastic():

    d = DeviceLoggingImplWithDBDirect()
    d.update_devices_to_be_logged("sdp-processing-controller")
    d.start_tracing()
    sleep(2)  
    d.stop_tracing()                                                                            
    res = d.get_messages_as_list_dict()
    assert_that(res).is_type_of(list)

@pytest.mark.skipif(local_elastic_disabled,reason="only enabled for dev purposes")
def test_log_multiple_devices_from_elastic():

    d = DeviceLoggingImplWithDBDirect()
    d.update_devices_to_be_logged(["sdp-processing-controller","helm-deploy"])
    d.start_tracing()
    sleep(2)  
    d.stop_tracing()                                                                            
    res = d.get_messages_as_list_dict()
    for item in res:
        logging.info(item['ska_log_timestamp'])
    assert_that(res).is_type_of(list)

@pytest.mark.skipif(local_elastic_disabled,reason="only enabled for dev purposes")
def test_log_elastic_time_window():

    d = DeviceLoggingImplWithDBDirect()
    d.update_devices_to_be_logged("sdp-processing-controller")
    d.start_time = datetime.now() - timedelta(seconds=960)
    d._run_query()                                                                          
    res = d.get_messages_as_list_dict()
    for item in res:
        timestamp = item['ska_log_timestamp']
        lowest_minute = int(re.findall(r'(?<=^.{16}:)(\d{2})',timestamp)[0])
        current_minute = datetime.now().minute 
        break
    assert_that(current_minute - lowest_minute).is_less_than_or_equal_to(30)



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
@pytest.mark.skipif(local_elastic_disabled)
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
    d1 = DeviceLogging('DeviceLoggingImplWithDBDirect')
    d2 = DeviceLogging('DeviceLoggingImplWithDBDirect')
    d1.implementation.get_messages_as_list_dict = get_messages_as_list_dict_mock1
    d2.implementation.get_messages_as_list_dict = get_messages_as_list_dict_mock2
    fixture['mocked_device_logging_with_dummy_data'] = d1
    fixture['mocked_device_logging_with_empty_data'] = d2
    fixture['dummy_data'] = dict_results
    yield fixture
    ##tear down
    if os.path.isfile('build/{}'.format(filename_csv)):
        os.remove('build/{}'.format(filename_csv))
    if os.path.isfile('build/{}'.format(filename_json)):
        os.remove('build/{}'.format(filename_json))

@pytest.mark.skipif(local_elastic_disabled,reason="only enabled for dev purposes")
def test_print_to_csv_file(device_logging_fixture):
    #given
    d = device_logging_fixture['mocked_device_logging_with_dummy_data']
    filename = device_logging_fixture['filename_csv']
    dummy_data = device_logging_fixture['dummy_data']
    #when
    d.implementation.print_log_to_file(filename,style='csv')
    #then
    with open('build/{}'.format(filename), 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        results = []
        for row in reader:
            results.append(row)
    assert_that(results).is_equal_to(dummy_data)

@pytest.mark.skipif(local_elastic_disabled,reason="only enabled for dev purposes")
def test_print_to_json_file(device_logging_fixture):
    #given
    d = device_logging_fixture['mocked_device_logging_with_dummy_data']
    filename = device_logging_fixture['filename_json']
    dummy_data = device_logging_fixture['dummy_data']
    #when
    d.implementation.print_log_to_file(filename,style='dict')
    #then
    with open('build/{}'.format(filename), 'r') as file:
        results = json.loads(file.read())
    assert_that(results).is_equal_to(dummy_data)

@pytest.mark.skipif(local_elastic_disabled,reason="only enabled for dev purposes")
def test_print_json_empty_file(device_logging_fixture):
    #given
    d = device_logging_fixture['mocked_device_logging_with_empty_data']
    filename = device_logging_fixture['filename_json']
    #when
    d.implementation.print_log_to_file(filename,style='dict')
    #then
    with open('build/{}'.format(filename), 'r') as file:
        results = json.loads(file.read())
    assert_that(results).is_equal_to("no data logged")

@pytest.mark.skipif(local_elastic_disabled,reason="only enabled for dev purposes")
def test_print_csv_empty_file(device_logging_fixture):
    #given
    d = device_logging_fixture['mocked_device_logging_with_empty_data']
    filename = device_logging_fixture['filename_csv']
    #when
    d.implementation.print_log_to_file(filename,style='csv')
    #then
    with open('build/{}'.format(filename), 'r') as file:
        results = json.loads(file.read())
    assert_that(results).is_equal_to("no data logged")


'''def test_log_by_time_window_query():

    d = DeviceLogging('DeviceLoggingImplWithDBDirect')
    d.update_traces(['ska_mid/tm_subarray_node/1','mid_csp/elt/subarray_01','mid_sdp/elt/subarray_1'])
    d.implementation._search_filtered_by_timewindow(60*100)                                                                           
    res = d.get_messages_as_list_dict()
    for item in res:
        logging.info("cont: {}".format(item['container']))

def test_elastic():
    es = get_log_stash_db()
    index = "logstash-{}".format(date.today().strftime("%Y.%m.%d"))
    greater_than_query = 'now-{:d}s/s'.format(60*100)
    container_name = 'sdp-subarray-1'
    search = Search(using=es,index=index)\
        .filter("range",ska_log_timestamp={'gte': greater_than_query})\
        .query(Q("match_prhase",kubernetes__container_name=container_name))\
        .sort("ska_log_message")\
        .source(includes=['ska_log_message','ska_log_timestamp','kubernetes.container_name','kubernetes.pod_name'])
    for hit in search.scan():
        logging.info(hit.kubernetes.container_name)'''