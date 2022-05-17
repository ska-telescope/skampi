"""Pytest fixtures and bdd step implementations specific to dishes integration tests."""
import os
import pytest

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

from resources.models.dish_model.entry_point import (
    DishEntryPoint,
    set_execution_context,
)

from .. import conftest


@pytest.fixture(name="set_dishes_entry_point", autouse=True)
def fxt_set_entry_point(
    set_session_exec_env: fxt_types.set_session_exec_env,
    sut_settings: conftest.SutTestSettings,
):
    """Fixture to use for setting up the entry point as from only the interface to sdp."""
    exec_env = set_session_exec_env
    exec_env.entrypoint = DishEntryPoint
    #  TODO  determine correct scope for readiness checks to work
    exec_env.scope = ["Dish"]


@pytest.fixture(name="set_global_exec_settings")
def fxt_set_global_exec_settings(
    exec_settings: fxt_types.exec_settings,
):
    exec_settings.time_out = 100


@pytest.fixture(name="dish_start_up_test_exec_settings", autouse=True)
def fxt_dish_start_up_test_exec_settings(
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """General startup test execution settings specific to telescope from tmc.

    :param exec_settings: Fixture as used by skallop
    """
    integration_test_exec_settings.time_out = 100
    # we also make integration tests globally available to our model
    set_execution_context(integration_test_exec_settings)


# log checking


@pytest.fixture(name="set_up_subarray_log_checking_for_dishes", autouse=True)
@pytest.mark.usefixtures("set_dishes_entry_point")
def fxt_set_up_log_capturing_for_cbf(
    log_checking: fxt_types.log_checking, sut_settings: conftest.SutTestSettings
):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        assert tel.skamid
        dishes = tel.skamid.dishes(sut_settings.receptors)
        log_checking.capture_logs_from_devices(*dishes.list)


# resource configurations


@pytest.fixture(name="base_composition")
def fxt_sdp_base_composition(
    running_telescope,  # type: ignore
    sut_settings: conftest.SutTestSettings,
    entry_point: DishEntryPoint,
) -> list[int]:
    """Setup a base composition configuration to use for in a generic subarray composition for ska mid.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    # we set the the composition in terms of dishes to assign
    # we set this as an argument on the entrypoint even though
    # it also gets passed as an argument in the command
    # this is because the waiting needs to be specifically
    # for the dishes also which does not take dish ids as an argument
    # Future update in skallop should rather change the arguments for wait
    # to also uses nr of dishes as an argument
    entry_point.dishes_to_assign = [1, 2]
    return sut_settings.receptors


# scan configurations


@pytest.fixture(name="dish_base_configuration")
def fxt_dish_base_configuration(
    running_telescope: fxt_types.running_telescope,
    tmp_path: str,
    base_composition,  # type: ignore
    entry_point: fxt_types.entry_point,
) -> conf_types.ScanConfiguration:
    """Setup a base scan configuration to use for sdp.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    configuration = conf_types.ScanConfigurationByFile(
        tmp_path, conf_types.ScanConfigurationType.STANDARD
    )
    # cast(DishEntryPoint, entry_point).set_stackable_context(running_telescope)
    return configuration
