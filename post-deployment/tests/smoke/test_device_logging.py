from resources.test_support.helpers import DeviceLogging,DeviceLoggingImplWithDBDirect, get_log_stash_db
import logging
import json
import pytest
from assertpy import assert_that
from time import sleep
import re
import datetime 
from datetime import date
import mock
import os
import csv

###to be  moved
from elasticsearch_dsl import Search,Q


@pytest.mark.tracer
def test_device_logging():
    d = DeviceLogging()
    d.update_traces(['sys/tg_test/1'])
    logging.debug('starting traces for sys/tg_test/1')
    d.start_tracing()
    d.wait_until_message_received("DataGenerator::generating data", 20)
    dict_messages_before = d.get_messages_as_list_dict()
    d.stop_tracing()
    d = DeviceLogging("TraceHelper")
    d.update_traces(['sys/tg_test/1'])
    logging.debug('starting traces again for for sys/tg_test/1')
    d.start_tracing()
    sleep(3)
    dict_messages_after = d.get_messages_as_list_dict()
    d.stop_tracing()
    assert_that(dict_messages_before).is_not_equal_to(dict_messages_after)



def test_logging_on_test_device_as_string():
    d = DeviceLogging()
    d.update_traces(['sys/tg_test/1'])
    logging.debug('starting traces for sys/tg_test/1')
    d.start_tracing()
    d.wait_until_message_received("DataGenerator::generating data", 20)
    printeable_messages = d.get_printable_messages()
    assert_that(printeable_messages).is_instance_of(str)
    assert_that(printeable_messages).contains("DataGenerator::generating data")


def test_throw_error_():
    with pytest.raises(Exception):
        DeviceLogging("wrong implementation")
    DeviceLogging("TraceHelper")

def test_log_single_device_from_elastic():

    d = DeviceLoggingImplWithDBDirect()
    d.update_devices_to_be_logged("sdp-processing-controller")
    d.start_tracing()
    sleep(2)  
    d.stop_tracing()                                                                            
    res = d.get_messages_as_list_dict()
    assert_that(res).is_type_of(list)

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

def test_log_elastic_time_window():

    d = DeviceLoggingImplWithDBDirect()
    d.update_devices_to_be_logged("sdp-processing-controller")
    d._search_filtered_by_timewindow(960)                                                                           
    res = d.get_messages_as_list_dict()
    for item in res:
        timestamp = item['ska_log_timestamp']
        lowest_minute = int(re.findall(r'(?<=^.{16}:)(\d{2})',timestamp)[0])
        current_minute = datetime.datetime.now().minute 
        break
    assert_that(current_minute - lowest_minute).is_less_than_or_equal_to(960/60)



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



@mock.patch('resources.test_support.helpers.DeviceLoggingImplWithDBDirect.get_messages_as_list_dict')
def test_print_to_file(get_messages_as_list_dict_mock,print_to_file_fixture):
    #given
    get_messages_as_list_dict_mock.return_value = print_to_file_fixture['mock_results']
    d = DeviceLogging('DeviceLoggingImplWithDBDirect')
    filename = print_to_file_fixture['filename_json']
    #when
    d.implementation.print_log_to_file(filename)
    #then
    with open('build/{}'.format(filename), 'r') as file:
        results = json.loads(file.read())
    assert_that(results).is_equal_to(print_to_file_fixture['mock_results'])
    #and when
    filename = print_to_file_fixture['filename_csv']
    d.implementation.print_log_to_file(filename,style='csv')
    #then
    with open('build/{}'.format(filename), 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        results = []
        for row in reader:
            results.append(row)
    assert_that(results).is_equal_to(print_to_file_fixture['mock_results'])





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