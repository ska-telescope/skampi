import logging

# import os

import pytest
# import tango
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

@when("I configure alarm for Telescope with empty observation state")
def configure_alarm_for_empty_obs_state():
    alarm_handler = get_device_proxy("alarm/handler/01")
    alarm_formula = "tag=subarray_empty;formula=(ska_mid/tm_subarray_node/1/obsstate == 2);priority=log;group=none;message=(\"alarm for subarray node empty\")"
    alarm_handler.command_inout("Load", alarm_formula)
    
@then("alarm should be raised with UNACK state")
def validate_alarm_state(sut_settings: SutTestSettings):
    # tel = names.TEL()
    # subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    # subarray_obsstate = subarray.read_attribute("obsState").value
    # logger.info("SUBARRAY Value {}".format(subarray_obsstate))
    # logger.info("SUBARRAY ID: {}".format(sut_settings.subarray_id))
    
    alarm_handler = get_device_proxy("alarm/handler/01")
    alarm_summary = alarm_handler.read_attribute("alarmSummary").value
    
    logger.info("Alarm Summary {}".format(alarm_summary))
    assert "state=UNACK" in alarm_summary[0]

