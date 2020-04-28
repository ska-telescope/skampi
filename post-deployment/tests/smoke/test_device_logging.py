from resources.test_support.helpers import DeviceLogging
import logging
import json
import pytest
from assertpy import assert_that
from time import sleep
import os

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


def get_log_stash_db(port=9200,elastic_name='elastic-logging'):
    from elasticsearch import Elasticsearch
    
    HELM_RELEASE = os.environ.get('HELM_RELEASE')
    elastic_host = '{}-{}'.format(elastic_name,HELM_RELEASE)
    elastic_port = port
    host_details = {
        'host': elastic_host, 
        'port': elastic_port
    }  
    return Elasticsearch([host_details]) 

def __aggregate_by_or(list):
    import functools 
    return functools.reduce(lambda a,b: a|b,list)

class DeviceLoggingImplWithDBDirect():
    
    
    def __init__(self,es=None):
        from elasticsearch_dsl import Search,Q
        from datetime import date
        
        if es == None:
            es = get_log_stash_db()
        self.es=es
        #assumes the search is always only on todays logs
        index = "logstash-{}".format(date.today().strftime("%Y.%m.%d"))
        self.search = Search(using=es,index=index)
        self.containers_to_devices ={}
        self.Qs = None
        self.start_time=None
        self.running = False
    
    def start_tracing(self):
        from time import time
        self.start_time = time()
        self.running = True

    def _update_containers_to_devices(self,device,container):
        if device in self.containers_to_devices.keys():
            self.containers_to_devices[container] += "/{}".format(device)
        else:
            self.containers_to_devices[container] = device

    def _update_Q(self,device):
        from resources.test_support.mappings import device_to_container
        from elasticsearch_dsl import Search,Q

        container = device_to_container[device]
        self._update_containers_to_devices(device,container)
        if self.Qs == None:
            self.Qs = Q("match",kubernetes__container_name=container)
        else:
            self.Qs = self.Qs|Q("match",kubernetes__container_name=container)
    
    def stop_tracing(self):
        from time import time
        from math  import ceil
        if self.running:
            self.running = False
            self.elapsed_time = ceil(time() - self.start_time)

    def update_devices_to_be_logged(self,devices):
        if type(devices) == list:
            for device in devices:
                self._update_Q(device)
        if type(devices) == str:
            self._update_Q(devices)
    
    def get_messages_as_list_dict(self):
        from time import time
        from math  import ceil
        if self.running:
            self.stop_tracing()
        else:
            elapsed_time = ceil(time() - self.start_time)
        less_than_query = 'now-{:d}s/s'.format(elapsed_time)
        result =  self.search.filter("range",ska_log_timestamp={'lte': less_than_query}).\
            query(self.Qs).\
            execute()
        dict = [
            {
                "ska_log_message" : hit.ska_log_message,
                "ska_log_timestamp" : hit.ska_log_timestamp,
                "container" : hit.kubernetes.container_name,
                "device" : self.containers_to_devices[hit.kubernetes.container_name]
            }
            for hit in result
        ]
        return dict

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
    d.update_devices_to_be_logged(["sdp-processing-controller","mid_sdp/elt/master"])
    d.start_tracing()
    sleep(2)  
    d.stop_tracing()                                                                            
    res = d.get_messages_as_list_dict()
    logging.info(res)
    assert_that(res).is_type_of(list)

