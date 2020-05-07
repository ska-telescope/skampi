from elasticsearch_dsl import Search,Q, Index
from elasticsearch_dsl.query import Terms, Filtered,Range
from elasticsearch import Elasticsearch
from resources.test_support.mappings import device_to_container
import pprint
from datetime import date
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


def q_get_by_time(time):
    return Range(ska_log_timestamp={'gte':time})

def q_get_devices(devices):
    containers = [device_to_container[device] for device in devices]
    return Terms(kubernetes__container_name = containers)


 
####typical device sets
subarray_devices = [
        'ska_mid/tm_subarray_node/1',
        'mid_csp/elt/subarray_01',
        'mid_csp_cbf/sub_elt/subarray_01',
        'mid_sdp/elt/subarray_1']

### typical field sets
device_field_set = ['ska_log_message',
                    'ska_log_timestamp',
                    'kubernetes.container_name',
                    'kubernetes.pod_name',
                    'ska_tags']

###common chains
def get_logs_from_devices(time_window=60,devices = subarray_devices):
    s  = get_log_stash_search_for_today()
    result = s.query(f_results_per_time_window(time_window)).\
            query(q_get_devices(devices)).\
            sort('ska_log_timestamp').\
            source(device_field_set)
    for hit in result.scan():
        pprint.pprint(hit.to_dict()) 

def get_all_greater_than_time(time):
    s  = get_log_stash_search_for_today()
    result = s.query(q_get_by_time(time)).\
            sort('ska_log_timestamp').\
            source(device_field_set)
    pprint.pprint(result.execute.to_dict())

def get_mapping():
    index_name = get_log_stash_index_for_today()
    i = Index(index_name)
    return i

    