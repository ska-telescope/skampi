
from elasticsearch import Elasticsearch
import logging
import os
from elasticsearch_dsl import Search,Q
from elasticsearch_dsl.query import Range,Terms,Term
from datetime import date,datetime

from time import time,sleep
from math  import ceil
import json 
import csv
#local dependencies
from resources.test_support.persistance_helping import print_dict_to_file,print_dict_to_csv_file
from resources.test_support.mappings import device_to_container
from resources.log_consumer.tracer_helper import TraceHelper
#SUT frameworks
from tango import LogLevel

LOGGER = logging.getLogger(__name__)

class DeviceLoggingImplWithTraceHelper():
    
    def __init__(self):
        self.tracer=TraceHelper()
       # self.tracer.disable_logging()
        self.tracer.reset_messages()
        self.traces=[]
        self.log_level=LogLevel.LOG_DEBUG
    
    def set_logging_level(self,level):
        mapping = {'DEBUG' : LogLevel.LOG_DEBUG,
                   'INFO' : LogLevel.LOG_INFO,
                   'WARNING': LogLevel.LOG_WARN,
                   'OFF': LogLevel.LOG_OFF,
                   'FATAL':LogLevel.LOG_FATAL}
        self.log_level=mapping[level]
    
    def update_traces(self,traces):
        if type(traces) == list:
            self.traces.extend(traces)
        if type(traces) == str:
            self.traces.append(traces)

    def start_tracing(self):
        for trace in self.traces:
            LOGGER.debug('setting traces for %s',trace)
            self.tracer.enable_logging(trace, self.log_level)

    def stop_tracing(self):
        for trace in self.traces:
            LOGGER.debug('stopping traces for %s',trace)
            self.tracer.disable_logging(trace)
    
    def get_logging(self):
        return self.tracer.get_messages()

    def wait_until_message_received(self,message, timeout):
        self.tracer.wait_until_message_received(message, timeout)

    def _format_event_data(self,e,format='string'):
        if format=='string':
            message =" reception date: {} message: '{}' error:{}".\
                format(
                    e.reception_date,
                    e.attr_value.value,
                    e.err
                )
        elif format=='dict':
            message = {
                'reception date':e.reception_date,
                'message':e.attr_value.value,
                'error': e.err}
        return message

    def get_printable_messages(self):
        messages = self.tracer.get_messages()
        msg_counter = 0
        printout = ''
        for message in messages:
            msg_counter +=1
            printout += str(msg_counter) + self._format_event_data(message) + "\n"
        return printout

    def get_messages_as_list_dict(self):
        messages = self.tracer.get_messages()
        return [self._format_event_data(message,format="dict") for message in messages]

#abstraction of Device logging implemenetation is set by implementation object and mappoing is defined in shim dictionary
class DeviceLogging():
    
    def __init__(self,implementation='TracerHelper'):
        if (implementation=='TracerHelper'):
            self.implementation = DeviceLoggingImplWithTraceHelper()
            self._shim = {"set_logging_level":self.implementation.set_logging_level,
                          "update_traces": self.implementation.update_traces, 
                          "stop_tracing": self.implementation.stop_tracing, 
                          "get_logging": self.implementation.get_logging, 
                          "start_tracing": self.implementation.start_tracing, 
                          "wait_until_message_received": self.implementation.wait_until_message_received, 
                          "get_printable_messages": self.implementation.get_printable_messages, 
                          "get_messages_as_list_dict": self.implementation.get_messages_as_list_dict
             }
        elif (implementation=='DeviceLoggingImplWithDBDirect'):
            self.implementation = DeviceLoggingImplWithDBDirect()
            self._shim = {"set_logging_level":self.implementation.set_logging_level,
                          "update_traces": self.implementation.update_devices_to_be_logged, 
                          "stop_tracing": self.implementation.stop_tracing, 
                          "get_logging": self.implementation.get_logging, 
                          "start_tracing": self.implementation.start_tracing, 
                          "wait_until_message_received": self.implementation.wait_until_message_received, 
                          "get_printable_messages": self.implementation.get_printable_messages, 
                          "get_messages_as_list_dict": self.implementation.get_messages_as_list_dict
             }
        else:
            raise Exception('unknown implentation of Device logging {}'.format(implementation))

    def set_logging_level(self,level):
        self._shim['set_logging_level'](level)
    
    def update_traces(self,traces):
        self._shim['update_traces'](traces)

    def start_tracing(self):
        self._shim['start_tracing']()

    def stop_tracing(self):
        self._shim['stop_tracing']()
    
    def get_logging(self):
        return self._shim['get_logging']()

    def wait_until_message_received(self,message, timeout):
        self._shim['wait_until_message_received'](message, timeout)

    def get_printable_messages(self):
        return self._shim['get_printable_messages']()

    def get_messages_as_list_dict(self):
        return self._shim['get_messages_as_list_dict']()


class DeviceLoggingImplWithDBDirect():

    def __init__(self,es=None):
 
        if es == None:
            self.local = self.is_local()
            if self.local:
                es = Elasticsearch([{
                        'host': '{}-{}'.format('elastic-logging',os.environ.get('HELM_RELEASE')), 
                        'port': 9200
                    }])
            else:
                es = Elasticsearch([{
                        'host': "192.168.93.94", 
                        'port': 9200
                    }])
        else:
            # injected es is assumed to be local
            self.local = True
        self.es=es
        #assumes the search is always only on todays logs
        if(self.local):
            index = "logstash-{}".format(date.today().strftime("%Y.%m.%d"))
        else:
            index = "filebeat-{}".format(date.today().strftime("%Y.%m.%d"))

        self.search = Search(using=es,index=index)
        self.containers_to_devices ={}
        self.Qs = None
        self.start_time=None
        self.running = False
        self.source_includes = ['ska_log_message','ska_log_timestamp','kubernetes.container_name','kubernetes.pod_name']
    
    def is_local(self,port=9200,elastic_name='elastic-logging'):
        HELM_RELEASE = os.environ.get('HELM_RELEASE')
        elastic_host = '{}-{}'.format(elastic_name,HELM_RELEASE)
        tracer = TraceHelper()
        return tracer.check_port(elastic_host, port) == 0

    def start_tracing(self):   

        self.start_time = datetime.now()
        self.running = True

    def set_logging_level(self,level):
        #TODO implement filtering based on log level
        self.logging =level

    def get_logging(self):
        #TODO implement filtering based on log level
        return self.logging

    def wait_until_message_received(self,message,timeout):
        #returns immediately as this behaviour cant be done by this object
        return

    def _update_containers_to_devices(self,device,container):

        if container in self.containers_to_devices.keys():
            self.containers_to_devices[container] += "/{}".format(device)
        else:
            self.containers_to_devices[container] = device

    def _update(self,device):
        container = device_to_container[device]
        self._update_containers_to_devices(device,container)
    
    def _qeury_by_time_window(self):
        return Range(ska_log_timestamp={'gte':self.start_time})

    def _qeury_by_containers(self):
        containers = list(self.containers_to_devices.keys())
        if len(containers) == 1:
            return Term(kubernetes__container_name__keyword = containers[0])
        return Terms(kubernetes__container_name__keyword = containers)

    def _run_query(self):
        search = self.search\
            .query(self._qeury_by_time_window())\
            .query(self._qeury_by_containers())\
            .sort("ska_log_message")\
            .source(includes=self.source_includes)
        ##may be replaced by a to_dict command
        self.dict_results = []
        for hit in search.scan():
            ## following code is temp to remove spurios hits on container names using match instead of terms search
            ## TODO fix by using appropriate elastic query
            container = hit.kubernetes.container_name
            if container in self.containers_to_devices.keys():
                self.dict_results.append({
                    "ska_log_message" : hit.ska_log_message,
                    "ska_log_timestamp" : hit.ska_log_timestamp,
                    "container" : container,
                    "pod" : hit.kubernetes.pod_name,
                    "device" : self.containers_to_devices[hit.kubernetes.container_name]
            })

    def stop_tracing(self):

        self.running = False
        self._run_query()


    def update_devices_to_be_logged(self,devices):

        if type(devices) == list:
            for device in devices:
                self._update(device)  
        if type(devices) == str:
            self._update(devices)

    def get_messages_as_list_dict(self):

        if self.running:
            self.stop_tracing()
        
        return self.dict_results

    def _format_log_data(self,log):
        log =" reception date: {} device/comp: {} message: '{}' container: {} ".\
                format(
                    log['ska_log_timestamp'],
                    log['device'],
                    log['ska_log_message'],
                    log['container']   
                )
        return log

    def get_printable_messages(self):
        logs = self.get_messages_as_list_dict()
        log_counter = 0
        printout = ''
        for log in logs:
            log_counter +=1
            printout += str(log_counter) + self._format_log_data(log) + "\n"
        return printout
    
    def print_log_to_file(self,filename,style='dict'):
        data = self.get_messages_as_list_dict()
        if not os.path.exists('build'):
            os.mkdir('build')
        if data != []:
            if style=='dict':
                print_dict_to_file('build/{}'.format(filename),data)
            elif style=='csv':
                print_dict_to_csv_file('build/{}'.format(filename),data)
        else:
            data = 'no data logged'
            print_dict_to_file('build/{}'.format(filename),data)


                
