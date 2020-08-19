#from resources.test_support.event_waiting import watchSpec
#from resources.test_support.fixtures import running_telescope,resource_config_file,idle_subarray
#import resources.test_support.fixtures


import logging
from time import sleep
import pytest

LOGGER = logging.getLogger(__name__)
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish, ResourceAllocation


def test_configure_subarray(configured_subarray):
   pass
