import os, sys
import logging
import pytest
from assertpy import assert_that

from resources.test_support.helpers import resource, subarray_devices

LOGGER = logging.getLogger(__name__)

####typical device sets
# subarray_devices = [
#         'ska_mid/tm_subarray_node/1',
#         'mid_csp/elt/subarray_01',
#         'mid_csp_cbf/sub_elt/subarray_01',
#         'mid_sdp/elt/subarray_1']

@pytest.mark.first
@pytest.mark.last
def test_mvp_clean():
    for device in subarray_devices:
        LOGGER.info(f"{device} is in {resource(device).get('State')} state")
    for device in subarray_devices:
        LOGGER.info(f"{device} is in {resource(device).get('obsState')} obsState")

    assert_that(resource('mid_csp/elt/subarray_01').get('State')).is_equal_to(resource('ska_mid/tm_subarray_node/1').get('State'))
    assert_that(resource('ska_mid/tm_subarray_node/1').get('State')).is_equal_to(resource('mid_csp_cbf/sub_elt/subarray_01').get('State'))
    assert_that(resource('mid_csp/elt/subarray_01').get('State')).is_equal_to(resource('mid_csp_cbf/sub_elt/subarray_01').get('State'))
    