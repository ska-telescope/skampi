
"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""
import sys, os
import pytest
import logging
from time import sleep
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
from concurrent import futures
#SUT
from ska.scripting.domain import Telescope, SubArray
#SUT infrastructure
from tango import DeviceProxy, DevState
## local imports
from resources.test_support.helpers import resource
from resources.test_support.sync_decorators import sync_assign_resources, sync_obsreset,sync_abort,sync_scan_oet
from resources.test_support.persistance_helping import update_resource_config_file
from resources.test_support.controls import set_telescope_to_standby,set_telescope_to_running,telescope_is_in_standby,take_subarray, restart_subarray

DEV_TEST_TOGGLE = os.environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True

LOGGER = logging.getLogger(__name__)

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
    'mid_d0001/elt/master' : 'pointingState',
    'mid_d0002/elt/master' : 'pointingState',
    'mid_d0003/elt/master' : 'pointingState',
    'mid_d0004/elt/master' : 'pointingState'}


@pytest.fixture
def result():
    return {}

@pytest.mark.select
@pytest.mark.skamid
@pytest.mark.quarantine
@pytest.mark.trial
# @pytest.mark.skip(reason="feature not working consistently")
@scenario("XTP-4444.feature", "BDD test case for Abort command Invoked while subarry is in configuring")
def test_subarray_abort_in_configuring():
    """Abort subarray"""

@given("a running telescope upon which a previously configure scan is run")
def assign():
    LOGGER.info("Before starting the telescope checking if the telescope is in StandBy.")
    assert(telescope_is_in_standby())
    LOGGER.info("Telescope is in StandBy.")
    LOGGER.info("Invoking Startup Telescope command on the telescope.")
    set_telescope_to_running()
    LOGGER.info("Telescope is started successfully.")
    pilot, sdp_block = take_subarray(1).to_be_composed_out_of(2)
    LOGGER.info("Resources are assigned successfully on Subarray.")
    LOGGER.info("Invoking configure command on the Subarray.")
    take_subarray(1).and_configuring_by_file(sdp_block)
    LOGGER.info("Configure command is invoked on Subarray.")
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('CONFIGURING')


@when("I call abort command")
def abort_subarray():
    @sync_abort(200)
    def abort():
        LOGGER.info("Invoking ABORT command on the Subarray.")
        SubArray(1).abort()
        LOGGER.info("Abort command is invoked on subarray")
    abort()
    LOGGER.info("ABORT is successful on Subarray.")


@then("The subarray eventually transitions into obsState ABORTED")
def check_state():
    LOGGER.info("Checking the results")
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('ABORTED')
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('ABORTED')
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('ABORTED')



def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_mid/tm_subarray_node/1').get('State') == "ON"):
        if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "IDLE"):
            LOGGER.info("tearing down composed subarray (IDLE)")
            take_subarray(1).and_release_all_resources()
            LOGGER.info("Resources are deallocated successfully from Subarray.")
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "READY"):
        LOGGER.info("tearing down configured subarray (READY)")
        take_subarray(1).and_end_sb_when_ready().and_release_all_resources()
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "SCANNING"):
        LOGGER.warn("Subarray is still in SCANNING! Please restart MVP manually to complete tear down")
        restart_subarray(1)
        raise Exception("Unable to tear down test setup")
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "ABORTING"):
        LOGGER.warn("Subarray is still in ABORTING! Please restart MVP manually to complete tear down")
        restart_subarray(1)
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "ABORTED"):
        take_subarray(1).restart_when_aborted()
    LOGGER.info("Put Telescope back to standby")
    set_telescope_to_standby()
    LOGGER.info("Telescope is in StandBy.")