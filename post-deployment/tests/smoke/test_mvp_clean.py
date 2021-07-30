import time
import os, sys
import logging
import pytest
from assertpy import assert_that
from  functools import reduce
from resources.test_support.helpers import resource, subarray_devices

LOGGER = logging.getLogger(__name__)


####typical device sets
# subarray_devices = [
#         'ska_mid/tm_subarray_node/1',
#         'mid_csp/elt/subarray_01',
#         'mid_csp_cbf/sub_elt/subarray_01',
#         'mid_sdp/elt/subarray_1']

@pytest.mark.skamid
@pytest.mark.first
@pytest.mark.xfail 
def test_is_running(running_telescope):
    pass

@pytest.mark.trial
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
    LOGGER.info("Testing only for equality, omitting SDP states for now")

    LOGGER.info(
        'resource("ska_mid/tm_central/central_node").get("telescopeState")'
        + str(resource("ska_mid/tm_central/central_node").get("telescopeState"))
    )
    LOGGER.info(
        'resource("ska_mid/tm_subarray_node/1").get("State")'
        + str(resource("ska_mid/tm_subarray_node/1").get("State"))
    )
    LOGGER.info(
        'resource("mid_csp/elt/subarray_01").get("State")'
        + str(resource("mid_csp/elt/subarray_01").get("State"))
    )
    LOGGER.info(
        'resource("mid_sdp/elt/subarray_1").get("State")'
        + str(resource("mid_sdp/elt/subarray_1").get("State"))
    )
    LOGGER.info(
        'resource("mid_csp/elt/master").get("State")'
        + str(resource("mid_csp/elt/master").get("State"))
    )
    LOGGER.info(
        'resource("mid_sdp/elt/master").get("State")'
        + str(resource("mid_sdp/elt/master").get("State"))
    )
    LOGGER.info(
        'resource("ska_mid/tm_leaf_node/d0001").get("State")'
        + str(resource("ska_mid/tm_leaf_node/d0001").get("State"))
    )
    LOGGER.info(
        'resource("ska_mid/tm_leaf_node/d0002").get("State")'
        + str(resource("ska_mid/tm_leaf_node/d0002").get("State"))
    )
    LOGGER.info(
        'resource("ska_mid/tm_leaf_node/d0003").get("State")'
        + str(resource("ska_mid/tm_leaf_node/d0003").get("State"))
    )
    LOGGER.info(
        'resource("ska_mid/tm_leaf_node/d0004").get("State")'
        + str(resource("ska_mid/tm_leaf_node/d0004").get("State"))
    )
    LOGGER.info(
        'resource("mid_d0001/elt/master").get("State")'
        + str(resource("mid_d0001/elt/master").get("State"))
    )
    LOGGER.info(
        'resource("mid_d0002/elt/master").get("State")'
        + str(resource("mid_d0002/elt/master").get("State"))
    )
    LOGGER.info(
        'resource("mid_d0003/elt/master").get("State")'
        + str(resource("mid_d0003/elt/master").get("State"))
    )
    LOGGER.info(
        'resource("mid_d0004/elt/master").get("State")'
        + str(resource("mid_d0004/elt/master").get("State"))
    )

    assert 0

@pytest.mark.select   
@pytest.mark.last
def test_smell_mvp_after():
    test_smell_mvp("POST")