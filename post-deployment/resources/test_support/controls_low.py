import pytest
from datetime import date,datetime
import os
import logging

from resources.test_support.helpers_low import resource

LOGGER = logging.getLogger(__name__)

def telescope_is_in_standby():
    LOGGER.info('resource("ska_low/tm_subarray_node/1").get("State")'+ str(resource('ska_low/tm_subarray_node/1').get("State")))
    LOGGER.info('resource("ska_low/tm_leaf_node/mccs_master").get("State")' +
                str(resource('ska_low/tm_leaf_node/mccs_master').get("State")))
    LOGGER.info('resource("low-mccs/control/control").get("State")' +
                str(resource('low-mccs/control/control').get("State")))
    return  [resource('ska_low/tm_subarray_node/1').get("State"),
            resource('ska_low/tm_leaf_node/mccs_master').get("State"),
            resource('low-mccs/control/control').get("State")] == \
            ['OFF','OFF', 'OFF']