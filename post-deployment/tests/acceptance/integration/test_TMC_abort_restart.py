from tango import DeviceProxy
from datetime import date, datetime
import os
import pytest
import logging
from resources.test_support.helpers import waiter, watch, resource
from resources.test_support.controls import telescope_is_in_standby, set_telescope_to_standby
from resources.test_support.sync_decorators import sync_abort,time_it,sync_restart
import resources.test_support.tmc_helpers as tmc
from resources.test_support.logging_decorators import log_it

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

@pytest.mark.select
#@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
def test_abort_restart():
    try:
        # given an interface to TMC to interact with a subarray node and a central node
        fixture = {}
        fixture['state'] = 'Unknown'
        the_waiter=waiter()

        # given a started up telescope
        assert (telescope_is_in_standby())
        LOGGER.info('Staring up the Telescope')
        tmc.start_up()
        fixture['state'] = 'Telescope On'

        # and a subarray composed of two resources configured as perTMC_integration/assign_resources.json
        LOGGER.info('Composing the Subarray')
        tmc.compose_sub()
        fixture['state'] = 'Subarray Assigned'

        resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
        LOGGER.info('Aborting the subarray')
        fixture['state'] = 'Subarray ABORTING'
        @log_it('TMC_int_abort', devices_to_log, non_default_states_to_check)
        @sync_abort()
        def abort():
            resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
            resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
            SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
            SubarrayNode.Abort()
            LOGGER.info('Invoked Abort on Subarray')
        abort()
        the_waiter.wait()
        LOGGER.info('Abort is complete on Subarray')
        fixture['state'] = 'Subarray Aborted'

        fixture['state'] = 'Subarray Restarting'
        @sync_restart()
        def restart():
            resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
            # resource('mid_csp/elt/subarray_01').assert_attribute('obsState').equals('ABORTED')
            # resource('mid_sdp/elt/subarray_1').assert_attribute('obsState').equals('ABORTED')
            SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
            # the_waiter.wait()
            LOGGER.info("Subarray obsState before Aborted assertion check is: " + str(SubarrayNode.obsState))
            resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('ABORTED')
            SubarrayNode.restart()
            LOGGER.info("Subarray obsState is: " + str(SubarrayNode.obsState))
            LOGGER.info('Invoked restart on Subarray')
        restart()

        LOGGER.info('Restart is complete on Subarray')
        fixture['state'] = 'Subarray empty'

        tmc.set_to_standby()
        LOGGER.info('Invoked StandBy on Subarray')

        # tear down
        LOGGER.info('TMC-Abort-Restart tests complete: tearing down...')

    except:
        LOGGER.info('Tearing down failed test, state = {}'.format(fixture['state']))
        if fixture['state'] == 'Telescope On':
            tmc.set_to_standby()
        elif fixture['state'] == 'Subarray Assigned':
            tmc.release_resources()
            tmc.set_to_standby()
        elif fixture['state'] == 'Subarray ABORTING':
            #restart_subarray(1)
            raise Exception('unable to teardown subarray from being in ABORTING')
        elif fixture['state'] == 'Subarray Aborted':
            #restart_subarray(1)
            raise Exception('unable to teardown subarray from being in Aborted')
        elif fixture['state'] == 'Subarray Restarting':
            #restart_subarray(1)
            raise Exception('unable to teardown subarray from being in Restarting')
        elif fixture['state'] == 'Subarray empty':
            tmc.set_to_standby()
        pytest.fail("unable to complete test without exceptions")
