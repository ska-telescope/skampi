from tango import DeviceProxy
from datetime import date, datetime
import os
import pytest
import logging
from resources.test_support.helpers import waiter, watch, resource
from resources.test_support.controls import telescope_is_in_standby, set_telescope_to_standby
import resources.test_support.tmc_helpers as tmc
import time

DEV_TEST_TOGGLE = os.environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True

devices_to_log = [
    'ska_mid/tm_subarray_node/1',
    'mid_csp/elt/subarray_01',
    'mid_csp_cbf/sub_elt/subarray_01',
    'mid_sdp/elt/subarray_1',
    'mid_d0001/elt/master',
    'mid_d0002/elt/master',
    'mid_d0003/elt/master',
    'mid_d0004/elt/master']
non_default_states_to_check = {
    'mid_d0001/elt/master': 'pointingState',
    'mid_d0002/elt/master': 'pointingState',
    'mid_d0003/elt/master': 'pointingState',
    'mid_d0004/elt/master': 'pointingState'}

LOGGER = logging.getLogger(__name__)


def restart_subarray(param = 1):
    pass


@pytest.mark.select
@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
def test_abort():
    try:
        # given an interface to TMC to interact with a subarray node and a central node
        fixture = {}
        fixture['state'] = 'Unknown'

        # given a started up telescope
        assert (telescope_is_in_standby())
        LOGGER.info('Staring up the Telescope')
        tmc.start_up()
        fixture['state'] = 'Telescope On'

        # and a subarray composed of two resources configured as perTMC_integration/assign_resources.json
        LOGGER.info('Composing the Subarray')
        sdp_block = tmc.compose_sub()
        fixture['state'] = 'Subarray Assigned'

        def abort():
            resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
            resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
            SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
            SubarrayNode.Abort()
            LOGGER.info('Invoked Abort on Subarray')

        abort()
        fixture['state'] = 'Subarray Aborted'
        resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('ABORTED')
        # tear down
        LOGGER.info('TMC-Abort tests complete: tearing down...')

    except:
        LOGGER.info('Tearing down failed test, state = {}'.format(fixture['state']))
        if fixture['state'] == 'Telescope On':
            tmc.set_to_standby()
        elif fixture['state'] == 'Subarray Assigned':
            tmc.release_resources()
            tmc.set_to_standby()
        elif fixture['state'] == 'Subarray Aborted':
            LOGGER.info('Tearing down in , state = {}'.format(fixture['state']))
            restart_subarray(1)
            raise Exception("Unable to tear down test setup")
        LOGGER.info("Put Telescope back to standby")
        set_telescope_to_standby()
        LOGGER.info("Telescope is in standby")