from resources.test_support.state_checker import StateChecker, return_resource
import pytest
import mock
import logging
from assertpy import assert_that
import re
from time import sleep
from datetime import datetime

def mock_get(par):
    sleep(0.005)
    return "dummy state for {}".format(par)

@mock.patch('resources.test_support.state_checker.resource')
def test_non_threaded_loop(resource_mock):
    #given
    resource_mock.return_value.get = mock_get
    s = StateChecker([
        'dummy resource-1',
        'dummy resource-2',
        'dummy resource-3'],
        max_nr_of_records=10)
    #when
    s.run(threaded=False,resolution=0.1)
    #then
    res = s.get_records()
    assert_that(res).is_length(10)
    keys = list(res[0].keys())
    assert_that(keys).is_equal_to([
        'seq',
        'time_window',
        'dummy resource-1 state',
        'dummy resource-1 delta',
        'dummy resource-2 state',
        'dummy resource-2 delta',
        'dummy resource-3 state',
        'dummy resource-3 delta',])
    assert_that(
        [ record[keys[0]] for record in res] )\
        .is_equal_to(
        [ n+1 for n in range(10)]
    )
    assert_that(
        [ re.match('\d\d:\d\d:\d\d',record[keys[1]]) != None for record in res]).\
        is_equal_to(
        [ True for n in range(10) ]
    )
    logging.info(res[0][keys[2]])
    for n in range(2,6,2):
        assert_that(
            [   re.match('dummy state for ObsState',record[keys[n]]) != None for record in res]).\
            is_equal_to(
            [ True for n in range(10) ]
        )
    for n in range(3,7,2):
        assert_that(
            [   re.match('\d+\.\d{6}',record[keys[n]]) != None for record in res]).\
            is_equal_to(
            [ True for n in range(10) ]
        )
    start_time_window = datetime.strptime(res[0]['time_window'],'%H:%M:%S')
    end_time_window =  datetime.strptime(res[9]['time_window'],'%H:%M:%S')
    assert_that(end_time_window.second-start_time_window.second).is_equal_to(1)

    
    
