from resources.test_support.event_waiting import watchSpec
from resources.test_support.fixtures import running_telescope,resource_config_file,idle_subarray


import logging
from time import sleep
import pytest

LOGGER = logging.getLogger(__name__)
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish, ResourceAllocation

specs = [
    watchSpec('ska_mid/tm_subarray_node/1','obsState'),        
    watchSpec('mid_csp/elt/subarray_01','obsState'),
    watchSpec('mid_csp_cbf/sub_elt/subarray_01','obsState')]


def test_configure_subarray(idle_subarray):
   pass