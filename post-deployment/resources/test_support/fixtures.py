# third party dependencies
import logging
from contextlib import contextmanager
import pytest
# direct dependencies
from resources.test_support.helpers import resource
from resources.test_support.event_wating import sync_telescope_shutting_down,watchSpec,sync_telescope_starting_up
from resources.test_support.persistance_helping import update_resource_config_file,load_config_from_file
# MVP code
from oet.domain import SKAMid

LOGGER = logging.getLogger(__name__)

# state asserting
def assert_telescope_is_standby():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('OFF')
    resource('mid_csp/elt/master').assert_attribute('State').equals('STANDBY')
    resource('ska_mid/tm_central/central_node').assert_attribute('State').equals('OFF')

def assert_telescope_is_running():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
    resource('mid_csp/elt/master').assert_attribute('State').equals('ON')
    resource('ska_mid/tm_central/central_node').assert_attribute('State').equals('ON')

@contextmanager
def wrap_assertion_as_predicate(predicate: bool):
    try:
        yield
    except:
        predicate = False

# state checkinhg
def is_telescope_standby() -> bool:
    predicate =  True
    with wrap_assertion_as_predicate(predicate):
        assert_telescope_is_standby()
    return predicate

def is_telescope_running() -> bool:
    predicate =  True
    with wrap_assertion_as_predicate(predicate):
        assert_telescope_is_running()
    return predicate

def set_telescope_to_running() -> None:
    # pre conditions
    assert_telescope_is_standby()
    # command
    with sync_telescope_starting_up(LOGGER,timeout=2):
        SKAMid().start_up()


def set_telescope_to_standby() -> None:
    # pre conditions

    # command
    with sync_telescope_shutting_down(LOGGER,timeout=4):
        SKAMid().standby()

## pytest fixtures
@pytest.fixture
def running_telescope() -> None:
    try:
        set_telescope_to_running()
    except Exception as e:
        if is_telescope_running():
            set_telescope_to_standby()
        raise e
    try:
        yield
        if is_telescope_running():
            set_telescope_to_standby()
    finally:
        pass
        # actions to do irrespective of errors



@pytest.fixture
def resource_config_file() -> str:
    assign_resources_file = 'resources/test_data/TMC_integration/assign_resources1.json'
    update_resource_config_file(assign_resources_file,disable_logging=True)
    config = load_config_from_file(assign_resources_file)
    yield config
