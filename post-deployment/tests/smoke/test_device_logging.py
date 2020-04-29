from resources.test_support.helpers import DeviceLogging,DeviceLoggingImplWithDBDirect
import logging
import json
import pytest
from assertpy import assert_that
from time import sleep
import re
import datetime 

###to be  moved



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
