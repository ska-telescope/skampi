"""Configure scan on telescope subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from resources.models.mvp_model.states import ObsState
from ..conftest import SutTestSettings


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.configure
@scenario("features/tmc_configure_scan.feature", "Configure the low telescope subarray using TMC")
def test_tmc_scan_on_low_subarray():
    """Scan on TMC low telescope subarray."""


@given("the Telescope is in ON state")
def telescope_is_in_on_state(running_telescope: fxt_types.running_telescope, ):
    """telescope is ON"""
    running_telescope.disable_automatic_setdown()
    return running_telescope


@given("the resources are assigned")
def the_resources_are_assigned(
    running_telescope: fxt_types.running_telescope,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """I assign resources to it."""

    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors
    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings, release_when_finished=False, 
        ):
            entry_point.compose_subarray(
                subarray_id, receptors, composition, sb_config.sbid
            )


