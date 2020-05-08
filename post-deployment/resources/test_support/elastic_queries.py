from elasticsearch_dsl import Search,Q, Index
from elasticsearch_dsl.query import Terms, Filtered,Range, Term, Match
from elasticsearch import Elasticsearch
from resources.test_support.mappings import device_to_container
import pprint
from datetime import date, timedelta,datetime
from  functools import reduce
import os

def get_Search(db,index):
    return Search(using=db,index=index)

def get_log_stash_index_for_today():
    return "logstash-{}".format(date.today().strftime("%Y.%m.%d"))

def f_results_per_time_window(time):
    greater_than_query = 'now-{:d}s/s'.format(time)
    return Range(ska_log_timestamp={'gte': greater_than_query})


def get_log_stash_db(port=9200,elastic_name='elastic-logging'):
    HELM_RELEASE = os.environ.get('HELM_RELEASE')
    elastic_host = '{}-{}'.format(elastic_name,HELM_RELEASE)
    elastic_port = port
    host_details = {
        'host': elastic_host, 
        'port': elastic_port
    }  
    return Elasticsearch([host_details]) 

def get_log_stash_search_for_today(port=9200,elastic_name='elastic-logging'):
    db = get_log_stash_db(port,elastic_name)
    index = get_log_stash_index_for_today()
    return get_Search(db,index)

## basic queries that return a query object to be inserted in the query method

def q_get_by_time(time):
    return Range(ska_log_timestamp={'gte':time})

def q_get_by_timewindow(start_time,end_time):
    return Range(ska_log_timestamp={'gte':start_time,'lte':end_time})

def q_get_devices(devices):
    if isinstance(devices,str):
        return q_get_device(devices)
    containers = [device_to_container[device] for device in devices]
    return Terms(kubernetes__container_name__keyword = containers)

def q_get_device(device):
    container = device_to_container[device]
    return Term(kubernetes__container_name__keyword = container)

def q_search_in_log_message(message):
    return Match(ska_log_message=message)

def get_mapping(field=None):
    index_name = get_log_stash_index_for_today()
    db = get_log_stash_db()
    i = Index(index_name,using=db)
    return i.get_mapping()
 
####typical device sets
subarray_devices = [
        'ska_mid/tm_subarray_node/1',
        'mid_csp/elt/subarray_01',
        'mid_csp_cbf/sub_elt/subarray_01',
        'mid_sdp/elt/subarray_1']

### typical columns for printout
mapping_keys1 = ['ska_log_timestamp','ska_tags','ska_log_message']

### typical field sets
device_field_set = ['ska_log_message',
                    'ska_log_timestamp',
                    'kubernetes.container_name',
                    'kubernetes.pod_name',
                    'ska_tags']

###common chains
def get_logs_from_devices(time,devices = subarray_devices,source_list=device_field_set):
    s  = get_log_stash_search_for_today()
    result = s.query(q_get_by_time(time)).\
            query(q_get_devices(devices)).\
            sort('ska_log_timestamp').\
            source(source_list)
    for hit in result.scan():
        pprint.pprint(hit.to_dict()) 

def get_all_greater_than_time(time):
    s  = get_log_stash_search_for_today()
    result = s.query(q_get_by_time(time)).\
            sort('ska_log_timestamp').\
            source(device_field_set)
    pprint.pprint(result.execute().to_dict())


def get_logs_from_devices_by_timewindow(start_time,end_time,devices = subarray_devices,source_list=device_field_set):
    s  = get_log_stash_search_for_today()
    result = s.query(q_get_by_timewindow(start_time,end_time)).\
            query(q_get_devices(devices)).\
            sort('ska_log_timestamp').\
            source(source_list)
    return ResultPrinter(result)

def get_most_recent_logs_from_devices(recent=60,devices = subarray_devices,source_list=device_field_set,search_for=None):
    end_time = datetime.now()
    start_time = end_time - timedelta(seconds=recent)
    return search_logs_from_devices_by_timewindow(start_time,end_time,devices,source_list,search_for)

def get_logs_from_devices_around_timewindow(time,delta_seconds=5,devices = subarray_devices,source_list=device_field_set,search_for=None):
    time = datetime.strptime(time,"%Y-%m-%dT%H:%M:%S.%fZ")   
    delta = timedelta(seconds=delta_seconds)
    start_time = time-delta
    end_time = time+delta
    return search_logs_from_devices_by_timewindow(start_time,end_time,devices,source_list,search_for)

def search_logs_from_devices_by_timewindow(start_time,end_time,devices = subarray_devices,source_list=device_field_set,search_for=None):
    s  = get_log_stash_search_for_today()
    if search_for == None:
        result = s.query(q_get_by_timewindow(start_time,end_time)).\
            query(q_get_devices(devices)).\
            sort('-ska_log_timestamp').\
            source(source_list)
    else:    
        result = s.query(q_get_by_timewindow(start_time,end_time)).\
            query(q_get_devices(devices)).\
            query(q_search_in_log_message(search_for)).\
            sort('-ska_log_timestamp').\
            source(source_list)
    return ResultPrinter(result)

def get_time_window(time,delta,direction='up_to'):
    if direction == 'up_to':
        return (time,time+delta)
    elif direction == 'from':
        return (time-delta,time)

### printing
class ResultPrinter():
    
    def __init__(self,result):
        self.result = result

    def get_top_level_keys(self):
        return self.result.execute()[0].to_dict().keys()

    def print_to_console(self,mapping_keys=mapping_keys1,seperator='\t',scan='short'):
        sep = seperator
        res = self.result
        if res.count() > 0:
            if mapping_keys == 'all':
                mapping_keys = self.get_top_level_keys()
            header = reduce(lambda x,y:x+'\t\t\t'+y,mapping_keys)
            print(header)
            if scan=='short':
                hits = res.execute()
                data = reduce(lambda x,y:x+'\n'+y,
                    [
                        reduce(lambda x,y: x+sep+y,[row[key] for key in row.to_dict().keys() if key in mapping_keys])
                        for row in hits
                    ]
                )
            else:
                data = reduce(lambda x,y:x+'\n'+y,
                    [
                        reduce(lambda x,y: x+sep+y,[row[key] for key in row.to_dict().keys() if key in mapping_keys])
                        for row in res.scan()
                    ]
                )
            print(data)
        else:
            print('search returned no results')


    