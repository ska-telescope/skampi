from resources.test_support.state_checker import StateChecker
from resources.test_support.helpers import resource
import pytest
import mock
import logging
from assertpy import assert_that
import re
from time import sleep,time
from datetime import datetime

def mock_get_unique(par):
    sleep(0.005)
    unique = time()
    return "dummy state {} {}".format(unique,par)

def mock_get_duplicate(par):
    sleep(0.005)
    return "{}".format(par)

def validate_results(res):

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
        'dummy resource-3 delta',
        'unique'])
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
    for n in range(2,6,2):
        assert_that(
            [   re.match('.+obsState',record[keys[n]]) != None for record in res]).\
            is_equal_to(
            [ True for n in range(10) ]
        )
    for n in range(3,7,2):
        assert_that(
            [   re.match('\d+\.\d{6}',record[keys[n]]) != None for record in res]).\
            is_equal_to(
            [ True for n in range(10) ]
        )
    assert_that(
        [ record[keys[8]] for record in res] )\
        .is_equal_to(
        [ True for n in range(10)]
    )
    start_time_window = datetime.strptime(res[0]['time_window'],'%H:%M:%S')
    end_time_window =  datetime.strptime(res[9]['time_window'],'%H:%M:%S')
    assert_that((end_time_window-start_time_window).seconds).is_close_to(1,1)

@mock.patch('resources.test_support.state_checker.resource')
def test_non_threaded_loop(resource_mock):
    #given
    resource_mock.return_value.get = mock_get_unique
    s = StateChecker([
        'dummy resource-1',
        'dummy resource-2',
        'dummy resource-3'],
        max_nr_of_records=10)
    #when
    s.run(threaded=False,resolution=0.1)
    #then
    res = s.get_records()
    validate_results(res)
    filtered_result = s.get_records(filtered=True)
    assert_that(filtered_result).is_length(10)
    
def test_threaded_loop():
    #give
    s = StateChecker([
        'ska_mid/tm_subarray_node/1'],
        max_nr_of_records=20)
    #when
    s.run(threaded=True,resolution=0.1)
    sleep(1)
    s.stop()
    #then
    res = s.get_records()
    assert_that(res).is_not_empty()
    
@mock.patch('resources.test_support.state_checker.resource')
def test_annotate_uniqueness(resource_mock):
    #given
    resource_mock.return_value.get = mock_get_duplicate
    s = StateChecker([
        'dummy resource-1',
        'dummy resource-2',
        'dummy resource-3'],
        max_nr_of_records=10)
    #when
    s.run(threaded=False,resolution=0.1)
    #then
    res = s.get_records()
    expected = [True]
    expected.extend([ False for n in range(9)])
    assert_that(
        [ record['unique'] for record in res] )\
        .is_equal_to(expected)
    filtered_result = s.get_records(filtered=True)
    assert_that(filtered_result).is_length(1)


@mock.patch('resources.test_support.state_checker.resource')
def test_time_window(resource_mock):
    #given
    resource_mock.return_value.get = mock_get_unique
    s = StateChecker([
        'dummy resource-1',
        'dummy resource-2',
        'dummy resource-3'],
        max_nr_of_records=10)
    #when
    s.run(threaded=False,resolution=0.1)
    #then
    records = s.get_records()
    for record in records:
        logging.info(record['time_window'])