from tango import DeviceProxy
from datetime import datetime
from resources.test_support.event_waiting import watchSpec,sync_subarray_assigning,sync_subarray_releasing
from resources.test_support.fixtures import running_telescope,resource_config_file

import logging
from time import sleep
import pytest

LOGGER = logging.getLogger(__name__)
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish, ResourceAllocation

specs = [
    watchSpec('ska_mid/tm_subarray_node/1','obsState'),        
    watchSpec('mid_csp/elt/subarray_01','obsState'),
    watchSpec('mid_csp_cbf/sub_elt/subarray_01','obsState')]


def test_assign_resources(running_telescope,resource_config_file):
    subArray = SubArray(1)
    with sync_subarray_assigning(1,LOGGER,10,log_enabled = True):
        LOGGER.info(f'\n{datetime.now().isoformat():<30} assigning resources')
        multi_dish_allocation = ResourceAllocation(dishes=[Dish(x) for x in range(1, 2 + 1)])
        subArray.allocate_from_file(resource_config_file, multi_dish_allocation)
    with sync_subarray_releasing(1,LOGGER,10,log_enabled = True):
        LOGGER.info(f'\n{datetime.now().isoformat():<30} releasing resources')
        subArray.deallocate()

