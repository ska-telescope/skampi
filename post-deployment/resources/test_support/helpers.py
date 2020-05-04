import sys

from tango import DeviceProxy, DevState, CmdArgType, EventType
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from time import sleep
import signal
from numpy import ndarray
import logging
import json 
from datetime import date
import random
import os
from random import choice
from resources.log_consumer.tracer_helper import TraceHelper
from tango import Database, DeviceProxy, DeviceData, EventType, LogLevel, DevVarStringArray,EventData, DeviceAttribute
from elasticsearch_dsl import Search,Q
from datetime import date
from time import time
from resources.test_support.mappings import device_to_container
from math  import ceil
from elasticsearch import Elasticsearch
import json
import csv

LOGGER = logging.getLogger(__name__)

obsState = {"IDLE": 0}


def map_dish_nr_to_device_name(dish_nr):
    digits = str(10000 + dish_nr)[1::]
    return "mid_d" + digits + "/elt/master"
    
def handlde_timeout():
    print("operation timeout")
    raise Exception("operation timeout")

class resource:
    device_name = None

    def __init__(self, device_name):
        self.device_name = device_name

    def get(self, attr):
        p = DeviceProxy(self.device_name)
        attrs = p.get_attribute_list()
        if (attr not in attrs): return "attribute not found"
        tp = p._get_attribute_config(attr).data_type
        if (tp == CmdArgType.DevEnum):
            return getattr(p, attr).name
        if (tp == CmdArgType.DevState):
            return str(p.read_attribute(attr).value)
        else:
            value = getattr(p, attr)
            if isinstance(value, ndarray):
                return tuple(value)
            return getattr(p, attr)


class monitor(object):
    previous_value = None
    resource = None
    attr = None
    device_name = None
    current_value = None

    def __init__(self, resource, previous_value, attr):
        self.previous_value = previous_value
        self.resource = resource
        self.attr = attr
        self.device_name = resource.device_name
        self.current_value = self.resource.get(self.attr)

    def _update(self):
        self.current_value = self.resource.get(self.attr)

    def _is_not_changed(self):
        comparison = (self.previous_value == self.current_value)
        if isinstance(comparison, ndarray):
            return comparison.all()
        else:
            return comparison

    def _wait(self, timeout=80):
        timeout = timeout
        while (self._is_not_changed()):
            timeout -= 1
            if (timeout == 0): return "timeout"
            sleep(0.1)
            self._update()
        return timeout

    def get_value_when_changed(self, timeout=50):
        response = self._wait(timeout)
        if (response == "timeout"):
            return "timeout"
        return self.current_value

    def wait_until_value_changed(self, timeout=50):
        return self._wait(timeout)


class subscriber:

    def __init__(self, resource):
        self.resource = resource

    def for_a_change_on(self, attr):
        value_now = self.resource.get(attr)
        return monitor(self.resource, value_now, attr)


def watch(resource):
    return subscriber(resource)


# this function may become depracated
class state_checker:

    def __init__(self, device, timeout=80, debug=False):
        self.device = device
        self.timeout = timeout
        self.debug = debug

    def to_be(self, *premises):  # a dictionary specifying the rule e.g {"attr" : "obsState", "value" : "IDLE" }
        timeout = self.timeout
        result = "notOK"
        while (timeout != 0):
            if (self.debug): print(timeout)
            premise_correct = False
            result = str(timeout)
            for premise in premises:
                required_attr = premise["value"]
                attr_name = premise["attr"]
                current_attr = self.device.get(attr_name)
                if (current_attr == required_attr):
                    premise_correct = True
                else:
                    premise_correct = False
                    result += str(attr_name) + " not eq " + str(required_attr)
            if (premise_correct):
                return timeout
                # TODO throw timout exception
            else:
                sleep(0.1)
                timeout -= 1
        return "timed out"


def wait_for(device, timeout=80):
    return state_checker(device, timeout)


def take_subarray(id):
    return pilot(id)


class pilot():

    def __init__(self, id):
        self.SubArray = SubArray(id)
        self.logs = ""

    def to_be_composed_out_of(self, dishes):
        the_waiter = waiter()
        the_waiter.set_wait_for_assign_resources()

        self.result = self.SubArray.allocate(ResourceAllocation(dishes=[Dish(x) for x in range(1, dishes + 1)]))

        the_waiter.wait()
        LOGGER.debug(the_waiter.logs)
        self.logs = the_waiter.logs
        assert(not the_waiter.timed_out)
        return self

    def and_configure_scan_by_file(self,file='resources/test_data/polaris_b1_no_cam.json'):
        timeout = 80
        # update the ID of the config data so that there is no duplicate configs send during tests
        update_file(file)
        signal.signal(signal.SIGALRM, handlde_timeout)
        signal.alarm(timeout)  # wait for 30 seconds and timeout if still stick
        try:
            logging.info("Configuring the subarray")
            SubArray(1).configure_from_file(file, with_processing=False)
        except Exception as ex_obj:
            LOGGER.info("Exception in configure command: %s", ex_obj)


def restart_subarray(id):
    pass


class waiter():

    def __init__(self):
        self.waits = []
        self.logs = ""
        self.timed_out = False

    def set_wait_for_assign_resources(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State"))
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("receptorIDList"))
        # self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).for_a_change_on("State"))

    def set_wait_for_tearing_down_subarray(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("receptorIDList"))
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("State"))

    def set_wait_for_going_to_standby(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).for_a_change_on("State"))
        # at the moment sdb does not go to standby
        # self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("State"))

    def set_wait_for_starting_up(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).for_a_change_on("State"))
        # self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("State"))

    def set_wait_for_ending_SB(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState"))

    def wait(self, timeout=80):
        self.logs = ""
        while self.waits:
            wait = self.waits.pop()
            result = wait.wait_until_value_changed(timeout)
            if result == "timeout":
                self.timed_out = True
                self.logs += wait.device_name + " timed out whilst waiting for " + wait.attr + " to change from " + str(
                    wait.previous_value) + " in " + str(timeout) + " seconds;"
            else:
                self.logs += wait.device_name + " changed " + str(wait.attr) + " from " + str(
                    wait.previous_value) + " to " + str(wait.current_value) + " after " + str(
                    timeout - result) + " tries ;"

def update_file(file):
    import os 
    try:
        os.chdir('post-deployment')
    except: # ignores if this is an error (assumes then that we are already on that directory)
        pass
    with open(file, 'r') as f:
        data = json.load(f)
    random_no = random.randint(100, 999)
    data['scanID'] = random_no
    data['sdp']['configure'][0]['id'] = "realtime-" + date.today().strftime("%Y%m%d") + "-" + str(choice
                                                                                                  (range(1, 10000)))
    fieldid = 1
    intervalms = 1400

    scan_details = {}
    scan_details["fieldId"] = fieldid
    scan_details["intervalMs"] = intervalms
    scanParameters = {}
    scanParameters[random_no] = scan_details

    data['sdp']['configure'][0]['scanParameters'] = scanParameters

    with open(file, 'w') as f:
        json.dump(data, f)

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
            logging.debug('setting traces for %s',trace)
            self.tracer.enable_logging(trace, self.log_level)

    def stop_tracing(self):
        for trace in self.traces:
            logging.debug('stopping traces for %s',trace)
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
    
    def __init__(self,implementation='TraceHelper'):
        if (implementation=='TraceHelper'):
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
        if (implementation=='DeviceLoggingImplWithDBDirect'):
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


def get_log_stash_db(port=9200,elastic_name='elastic-logging'):
    
    HELM_RELEASE = os.environ.get('HELM_RELEASE')
    elastic_host = '{}-{}'.format(elastic_name,HELM_RELEASE)
    elastic_port = port
    host_details = {
        'host': elastic_host, 
        'port': elastic_port
    }  
    return Elasticsearch([host_details]) 

class DeviceLoggingImplWithDBDirect():
        
    def __init__(self,es=None):
 
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

        self.start_time = time()
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

        if device in self.containers_to_devices.keys():
            self.containers_to_devices[container] += "/{}".format(device)
        else:
            self.containers_to_devices[container] = device

    def _update_Q(self,device):

        container = device_to_container[device]
        self._update_containers_to_devices(device,container)
        if self.Qs == None:
            self.Qs = Q("match",kubernetes__container_name=container)
        else:
            self.Qs = self.Qs|Q("match",kubernetes__container_name=container)
    
    def _search_filtered_by_timewindow(self,timewindow):

        greater_than_query = 'now-{:d}s/s'.format(timewindow)
        search = self.search\
            .filter("range",ska_log_timestamp={'gte': greater_than_query})\
            .query(self.Qs)\
            .sort("ska_log_message")\
            .source(includes=['ska_log_message','ska_log_timestamp','kubernetes.container_name','kubernetes.pod_name'])
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

        elapsed_time = ceil(time() - self.start_time)
        self.running = False
        self._search_filtered_by_timewindow(elapsed_time)


    def update_devices_to_be_logged(self,devices):

        if type(devices) == list:
            for device in devices:
                self._update_Q(device)
        if type(devices) == str:
            self._update_Q(devices)

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
                with open('build/{}'.format(filename), 'w') as file:
                    file.write(json.dumps(data)) 
            elif style=='csv':
                csv_columns = data[0].keys()
                with open('build/{}'.format(filename), 'w') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                    writer.writeheader()
                    for row in data:
                        writer.writerow(row)
        else:
            data = 'no data logged'
            with open('build/{}'.format(filename), 'w') as file:
                file.write(json.dumps(data)) 
                

