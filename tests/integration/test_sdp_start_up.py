"""Start up the sdp feature tests."""
import os
from typing import Any, Callable, Dict, List, cast

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.connectors import configuration as config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.mvp_control.entry_points.synched_entrypoint import (
    SynchedEntryPoint,
)
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

MOCK_SUT = False


class SDPEntryPoint(SynchedEntryPoint):
    """Derived Entrypoint scoped to SDP element."""

    def __init__(self) -> None:
        super().__init__()
        tel = names.TEL()
        self.sdp_master = config.get_device_proxy(tel.sdp.master)

    def set_telescope_to_running(self):
        self.sdp_master.command_inout("On")

    def abort_subarray(self, sub_array_id: int):
        pass

    def clear_configuration(self, sub_array_id: int):
        pass

    def compose_subarray(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        composition: base.Composition,
        sb_id: str,
    ):
        pass

    def configure_subarray(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        configuration: base.ScanConfiguration,
        sb_id: str,
        duration: float,
    ):
        pass

    def reset_subarray(self, sub_array_id: int):
        pass

    def scan(self, sub_array_id: int):
        pass

    def set_telescope_to_standby(self):
        self.sdp_master.command_inout("Standby")

    def tear_down_subarray(self, sub_array_id: int):
        pass


@pytest.fixture(name="setup_mock", autouse=True)
def fxt_set_env(mock_entry_point: fxt_types.mock_entry_point):
    @mock_entry_point.when_set_telescope_to_running
    def mck_set_telescope_to_running():
        mock_entry_point.model.sdp.set_states_for_telescope_running()

    @mock_entry_point.when_set_telescope_to_standby
    def mck_set_telescope_to_standby():
        mock_entry_point.model.sdp.set_states_for_telescope_standby()


@pytest.fixture(name="set_entry_point", scope="session")
def fxt_set_entry_point(set_session_exec_env: fxt_types.set_session_exec_env, request):
    exec_env = set_session_exec_env
    if not MOCK_SUT:
        exec_env.entrypoint = SDPEntryPoint
        exec_env.session_entry_point = SDPEntryPoint
    else:
        exec_env.entrypoint = "mock"
    exec_env.scope = ["sdp"]


@pytest.mark.skalow
@scenario("features/sdp_start_up_telescope.feature", "Start up the telescope")
def test_start_up_the_telescope():
    """Start up the telescope."""


@given("an SDP")
def a_sdp(set_entry_point):
    """a SDP."""


@when("I start up the telescope")
def i_start_up_the_telescope(
    standby_telescope: fxt_types.standby_telescope,
    entry_point: fxt_types.entry_point,
):
    """I start up the telescope."""
    with standby_telescope.wait_for_starting_up():
        entry_point.set_telescope_to_running()


@then("the sdp must be on")
def the_sdp_must_be_on():
    """the sdp must be on."""
    tel = names.TEL()
    sdp_master = config.get_device_proxy(tel.sdp.master)
    result = sdp_master.read_attribute("state").value
    assert_that(result).is_equal_to("ON")


def test_test(
    request: Any,
    _pytest_bdd_example: Dict,
    mock_entry_point: fxt_types.mock_entry_point,
):
    """Test the test using a mock SUT"""
    global MOCK_SUT  # pylint: disable=global-statement
    MOCK_SUT = True
    # pylint: disable-next=too-many-function-args
    test_start_up_the_telescope(request, _pytest_bdd_example)  # type: ignore
