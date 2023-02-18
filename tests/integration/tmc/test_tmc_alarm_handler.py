import logging

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.connectors.configuration import get_device_proxy

from ska_ser_skallop.mvp_fixtures.context_management import (
    TelescopeContext,
)
from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@pytest.mark.startup
@scenario("features/tmc_alarm_handler.feature", "Configure Alarm for EMPTY Observation State")
def test_tmc_alarm_handler_telescope_mid():
    """Configure Alarm for EMPTY Observation State in mid."""
    

@given("an TMC")
def a_tmc():
    """an TMC"""
    
@given("an telescope subarray", target_fixture="composition")
def a_telescope_subarray(
    set_up_subarray_log_checking_for_tmc, base_composition: conf_types.Composition  # type: ignore
) -> conf_types.Composition:
    """an telescope subarray."""
    return base_composition

@given("an alarm handler")
def an_alarm_handler():
    """an Alarm Handler"""

@when("I configure alarm for Telescope with idle observation state")
def configure_alarm_for_empty_obs_state():
    alarm_handler = get_device_proxy("alarm/handler/01")
    alarm_formula = "tag=subarray_idle;formula=(ska_mid/tm_subarray_node/1/obsstate == 2);priority=log;group=none;message=(\"alarm for subarray node idle\")"
    alarm_handler.command_inout("Load", alarm_formula)
    
@then("alarm should be raised with UNACK state")
def validate_alarm_state(sut_settings: SutTestSettings):
    import time
    time.sleep(5)
    
    alarm_handler = get_device_proxy("alarm/handler/01")
    alarm_unacknowledged = alarm_handler.read_attribute("alarmUnacknowledged").value
    
    logger.info("Alarm Summary {}".format(alarm_unacknowledged))
    assert "subarray_idle" in alarm_unacknowledged

