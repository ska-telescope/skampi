import time
import os, sys
import logging
import pytest
from assertpy import assert_that
from  functools import reduce
from resources.test_support.helpers import resource, subarray_devices
from ska_ser_skallop.utils import env

LOGGER = logging.getLogger(__name__)


####typical device sets
# subarray_devices = [
#         'ska_mid/tm_subarray_node/1',
#         'mid_csp/elt/subarray_01',
#         'mid_csp_cbf/sub_elt/subarray_01',
#         'mid_sdp/elt/subarray_1']

@pytest.mark.ping
def test_empty_ping():
    # this test is to just check testing framework can run a test
    pass

@pytest.mark.skip
@pytest.mark.first
@pytest.mark.xfail 
@pytest.mark.running_telescope
def test_is_running(running_telescope):
    pass

@pytest.mark.select
@pytest.mark.skamid
@pytest.mark.first
@pytest.mark.last
def test_smell_mvp(pre_or_post="#PRE"):
    time.sleep(10)
    header = f"\n###{pre_or_post}-TEST STATES###\n{'Device Name:':<34} {'State':<15}{'obsState':<15}\n"
    output = [f"{device:<35}{resource(device).get('State'):<15}{resource(device).get('obsState'):<15}" for device in subarray_devices]
    aggegate_output = reduce(lambda x,y:x +'\n'+y ,output)
    LOGGER.info(f'Current state of the MVP:{header+aggegate_output}')
    
    LOGGER.info("Check the States of the TMC devices")
    assert_that(resource('ska_mid/tm_central/central_node').get('State')).is_equal_to('ON')
    assert_that(resource('ska_mid/tm_subarray_node/1').get('State')).is_equal_to('ON')
    assert_that(resource('ska_mid/tm_subarray_node/2').get('State')).is_equal_to('ON')
    assert_that(resource('ska_mid/tm_subarray_node/3').get('State')).is_equal_to('ON')

    LOGGER.info("Check the States of the CSP devices")
    assert_that(resource('mid_csp/elt/master').get('State')).is_equal_to('STANDBY')
    assert_that(resource('mid_csp/elt/subarray_01').get('State')).is_equal_to('OFF')
    assert_that(resource('mid_csp/elt/subarray_02').get('State')).is_equal_to('OFF')
    assert_that(resource('mid_csp/elt/subarray_03').get('State')).is_equal_to('OFF')

    LOGGER.info("Check the States of the SDP devices")
    assert_that(resource('mid_sdp/elt/subarray_1').get('State')).is_equal_to('OFF')
    assert_that(resource('mid_sdp/elt/subarray_2').get('State')).is_equal_to('OFF')
    assert_that(resource('mid_sdp/elt/subarray_3').get('State')).is_equal_to('OFF')

    LOGGER.info("Check the States of the DISH devices")
    assert_that(resource('mid_d0001/elt/master').get('State')).is_equal_to('STANDBY')
    assert_that(resource('mid_d0002/elt/master').get('State')).is_equal_to('STANDBY')
    assert_that(resource('mid_d0003/elt/master').get('State')).is_equal_to('STANDBY')
    assert_that(resource('mid_d0004/elt/master').get('State')).is_equal_to('STANDBY')

@pytest.mark.select   
@pytest.mark.last
def test_smell_mvp_after():
    test_smell_mvp("POST")