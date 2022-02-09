"""Assign resources to subarray feature tests."""
import logging
import os

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState

logger = logging.getLogger(__name__)

RECEPTORS = [1, 2]
SUB_ARRAY_ID = 1


@pytest.fixture(name="assign_resources_test_exec_settings")
def fxt_start_up_test_exec_settings(
    exec_settings: fxt_types.exec_settings,
) -> fxt_types.exec_settings:
    """Set up test specific execution settings.

    :param exec_settings: The global test execution settings as a fixture.
    :return: test specific execution settings as a fixture
    """
    assign_resources_test_exec_settings = exec_settings.replica()
    assign_resources_test_exec_settings.time_out = 150
    if os.getenv("DEBUG"):
        exec_settings.run_with_live_logging()
        assign_resources_test_exec_settings.run_with_live_logging()
    elif os.getenv("LIVE_LOGGING"):
        assign_resources_test_exec_settings.run_with_live_logging()
    elif os.getenv("REPLAY_EVENTS_AFTERWARDS"):
        assign_resources_test_exec_settings.replay_events_afterwards()
    return assign_resources_test_exec_settings


# resource configurations


@pytest.fixture(name="sdp_base_composition")
def fxt_sdp_base_composition(tmp_path) -> conf_types.Composition:
    """Setup a base composition configuration to use for sdp.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    composition = conf_types.CompositionByFile(
        tmp_path, conf_types.CompositionType.STANDARD
    )
    return composition


@pytest.fixture(name="csp_base_composition")
def fxt_csp_base_composition(tmp_path) -> conf_types.Composition:
    """Setup a base composition configuration to use for csp/cbf.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    composition = conf_types.CompositionByFile(
        tmp_path, conf_types.CompositionType.STANDARD
    )
    return composition


# log capturing


@pytest.fixture(name="set_up_log_checking_for_sdp")
@pytest.mark.usefixtures("set_sdp_entry_point")
def fxt_set_up_log_capturing_for_cbf(log_checking: fxt_types.log_checking):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        sdp_subarray = str(tel.sdp.subarray(SUB_ARRAY_ID))
        log_checking.capture_logs_from_devices(sdp_subarray)


@pytest.fixture(name="set_up_log_checking_for_cbf")
@pytest.mark.usefixtures("set_cbf_entry_point")
def fxt_set_up_log_checking_for_cbf(log_checking: fxt_types.log_checking):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        cbf_subarray = str(tel.csp.cbf.subarray(SUB_ARRAY_ID))
        log_checking.capture_logs_from_devices(cbf_subarray)


@pytest.fixture(name="set_up_log_checking_for_csp")
@pytest.mark.usefixtures("set_csp_entry_point")
def fxt_set_up_log_checking_for_csp(log_checking: fxt_types.log_checking):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        csp_subarray = str(tel.csp.subarray(SUB_ARRAY_ID))
        log_checking.capture_logs_from_devices(csp_subarray)


@pytest.mark.skip("test fails see bug https://jira.skatelescope.org/browse/SKB-124")
@pytest.mark.skalow
@pytest.mark.assign
@scenario(
    "features/sdp_assign_resources.feature", "Assign resources to sdp subarray in low"
)
def test_assign_resources_to_sdp_subarray_in_low():
    """Assign resources to sdp subarray in low."""


@pytest.mark.skamid
@pytest.mark.assign
@scenario(
    "features/sdp_assign_resources.feature", "Assign resources to sdp subarray in mid"
)
def test_assign_resources_to_sdp_subarray_in_mid():
    """Assign resources to sdp subarray in mid."""


@pytest.mark.skamid
@pytest.mark.assign
@scenario(
    "features/cbf_assign_resources.feature", "Assign resources to CBF mid subarray"
)
def test_assign_resources_to_cbf_mid_subarray():
    """Assign resources to CBF mid subarray."""


@pytest.mark.skalow
@pytest.mark.assign
@scenario(
    "features/cbf_assign_resources.feature", "Assign resources to CBF low subarray"
)
def test_assign_resources_to_cbf_low_subarray():
    """Assign resources to CBF low subarray."""


@pytest.mark.skalow
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature", "Assign resources to CSP low subarray"
)
def test_assign_resources_to_csp_low_subarray():
    """Assign resources to CSP low subarray."""


@given("an CBF subarray", target_fixture="composition")
def an_cbf_subarray(
    assign_resources_test_exec_settings,  # pylint: disable=unused-argument
    set_cbf_entry_point,  # pylint: disable=unused-argument
    set_up_log_checking_for_cbf,  # pylint: disable=unused-argument
    csp_base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """an SDP subarray."""
    return csp_base_composition


@given("an CSP subarray", target_fixture="composition")
def an_csp_subarray(
    assign_resources_test_exec_settings,  # pylint: disable=unused-argument
    set_csp_entry_point,  # pylint: disable=unused-argument
    set_up_log_checking_for_csp,  # pylint: disable=unused-argument
    csp_base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """an SDP subarray."""
    return csp_base_composition


@given("an SDP subarray", target_fixture="composition")
def an_sdp_subarray(
    assign_resources_test_exec_settings,  # pylint: disable=unused-argument
    set_sdp_entry_point,  # pylint: disable=unused-argument
    set_up_log_checking_for_sdp,  # pylint: disable=unused-argument
    sdp_base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """an SDP subarray."""
    return sdp_base_composition


@when("I assign resources to it", target_fixture="message_board")
def i_assign_resources_to_it(
    running_telescope: fxt_types.running_telescope,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    assign_resources_test_exec_settings: fxt_types.exec_settings,
):
    """I assign resources to it."""

    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_allocating_a_subarray(
            SUB_ARRAY_ID, RECEPTORS, assign_resources_test_exec_settings
        ):
            entry_point.compose_subarray(
                SUB_ARRAY_ID, RECEPTORS, composition, sb_config.sbid
            )


@then("the subarray must be in IDLE state")
def the_subarray_must_be_in_idle_state():
    """the subarray must be in IDLE state."""
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(SUB_ARRAY_ID))
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.IDLE)


@then("the CBF subarray must be in IDLE state")
def the_cbf_subarray_must_be_in_idle_state():
    """the subarray must be in IDLE state."""
    tel = names.TEL()
    cbf_subarray = con_config.get_device_proxy(tel.csp.cbf.subarray(SUB_ARRAY_ID))
    result = cbf_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.IDLE)


@then("the CSP subarray must be in IDLE state")
def the_csp_subarray_must_be_in_idle_state():
    """the subarray must be in IDLE state."""
    tel = names.TEL()
    csp_subarray = con_config.get_device_proxy(tel.csp.subarray(SUB_ARRAY_ID))
    result = csp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.IDLE)


@pytest.mark.test_tests
@pytest.mark.usefixtures("setup_sdp_mock")
def test_test_sdp_assign_resources(
    run_mock, mock_entry_point: fxt_types.mock_entry_point
):
    """Test the test using a mock SUT"""
    run_mock(test_assign_resources_to_sdp_subarray_in_mid)
    mock_entry_point.spy.set_telescope_to_running.assert_called()
    mock_entry_point.spy.compose_subarray.assert_called()
    mock_entry_point.model.sdp.master.spy.command_inout.assert_called()
    mock_entry_point.model.sdp.subarray1.spy.command_inout.assert_called()
