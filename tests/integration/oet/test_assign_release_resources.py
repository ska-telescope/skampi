"""
test_XTP-776
----------------------------------
Tests for creating SBI (XTP-779), allocating resources from SBI (XTP-777)
"""

import logging
from os import environ

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from resources.models.mvp_model.states import ObsState
from ska_oso_oet_client.activityclient import ActivityAdapter
from ska_oso_scripting.objects import SubArray
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from ..conftest import SutTestSettings
from .oet_helpers import ScriptExecutor

logger = logging.getLogger(__name__)
EXECUTOR = ScriptExecutor()

kube_namespace = environ.get("KUBE_NAMESPACE", "test")
kube_host = environ.get("KUBE_HOST")
rest_cli_uri = f"http://{kube_host}/{kube_namespace}/api/v1.0"
activity_adapter = ActivityAdapter(rest_cli_uri)


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.k8s
@scenario(
    "features/oet_assign_release_resources.feature",
    "Creating a new SBI with updated SB IDs and PB IDs",
)
def test_sbi_creation():
    """
    Given the SKUID service is running
    When I tell the OET to run
     file:///scripts/create_sbi.py using data/mid_sb_example.json
    Then the script completes successfully
    """


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.k8s

@scenario(
    "features/oet_assign_release_resources.feature",
    "Allocating resources with a SBI",
)
def test_resource_allocation():
    """
    Given an OET
    And  sub-array is in ObsState EMPTY
    When I tell the OET to allocate resources using
     script file:///scripts/allocate_from_file_mid_sb.py
     and SBI data/mid_sb_example.json
    Then the sub-array goes to ObsState IDLE
    """


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.k8s

@scenario(
    "features/oet_assign_release_resources.feature",
    "Releasing all resources from sub-array",
)
def test_resource_release():
    """
    Given sub-array with resources allocated to it
    When I tell the OET to release resources
     using script git:///scripts/deallocate.py
    Then the sub-array goes to ObsState EMPTY
    """


@given("an OET")
def a_oet():
    """an OET"""


@given("sub-array is in ObsState EMPTY")
def the_subarray_must_be_in_empty_state(
    running_telescope: fxt_types.running_telescope,
    sut_settings: SutTestSettings,
):
    """
    the subarray must be in EMPTY state.
    :param running_telescope: Dictionary containing the running telescope's devices
    :param sut_settings: A class representing the settings for the system under test.
    """
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.EMPTY)


@given("sub-array with resources allocated to it")
def the_subarray_with_recources_allocate(
    allocated_subarray: fxt_types.allocated_subarray,
    sut_settings: SutTestSettings,
):
    """
    the subarray must be in IDLE state.

    :param allocated_subarray: The allocated subarray to be configured.
    :param sut_settings: A class representing the settings for the system under test.
    """
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)

    central_node = con_config.get_device_proxy(tel.tm.central_node)
    assert str(central_node.read_attribute("telescopeState").value) == "ON"


@when(parsers.parse("I tell the OET to create SBI using script {script} and SB {sb_json}"))
def when_create_sbi(
    script,
    sb_json,
    context_monitoring: fxt_types.context_monitoring,
):
    """
    Use the OET Rest API to run a script that creates SBI from given SB.

    :param script: file path to an observing script
    :type script: str
    :param sb_json: file path to a scheduling block
    :type sb_json: str
    :param context_monitoring: An instance of the ContextMonitoring class
        containing context monitoring settings.
    """
    with context_monitoring.observe_while_running():
        script_completion_state = EXECUTOR.execute_script(script, sb_json)
        assert script_completion_state == "COMPLETE", (
            "Expected SBI creation script to be COMPLETED, instead was"
            f" {script_completion_state}"
        )


@when(
    parsers.parse(
        "I tell the OET to allocate resources using script {script} and SBI" " {sb_json}"
    )
)
def when_allocate_resources_from_sbi(
    script,
    sb_json,
    context_monitoring: fxt_types.context_monitoring,
    running_telescope: fxt_types.running_telescope,
    sut_settings: SutTestSettings,
    exec_settings: fxt_types.exec_settings,
):
    """
    Use the OET Rest API to run script that allocates resources from given SBI.

    :param script: file path to an observing script
    :param sb_json: file path to a scheduling block
    :param context_monitoring: for context monitoring
    :param running_telescope: A fixture for running telescope
    :param sut_settings: A class representing the settings for the system under test.
    :param exec_settings: A class representing the execution settings for the script.
    """
    with context_monitoring.context_monitoring():
        running_telescope.release_subarray_when_finished(
            sut_settings.subarray_id, sut_settings.receptors, exec_settings
        )
        script_completion_state = EXECUTOR.execute_script(script, sb_json)
        assert script_completion_state == "COMPLETE", (
            "Expected resource allocation script to be COMPLETED, instead was"
            f" {script_completion_state}"
        )


@when(parsers.parse("I tell the OET to release resources using script {script}"))
def when_release_resources(
    script,
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
):
    """
    Use the OET Rest API to run script that releases all resources.

    :param script: file path to an observing script
    :type script: str
    :param context_monitoring: An instance of the ContextMonitoring class
        containing context monitoring settings.
    :param allocated_subarray: The allocated subarray to be configured.


    """
    allocated_subarray.disable_automatic_teardown()
    with context_monitoring.context_monitoring():
        script_completion_state = EXECUTOR.execute_script(script)
        assert script_completion_state == "COMPLETE", (
            "Expected resource allocation script to be COMPLETED, instead was"
            f" {script_completion_state}"
        )


@when("I tell the OET to release resources")
def when_release_all_resources(
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    Use the OET Rest API to run script that releases all resources.
    :param context_monitoring: An instance of the ContextMonitoring class
        containing context monitoring settings.
    :param allocated_subarray: The allocated subarray to be configured.
    :param integration_test_exec_settings: integration test execution settings object
    """
    subarray_id = allocated_subarray.id

    with context_monitoring.context_monitoring():
        with allocated_subarray.wait_for_releasing_a_subarray(integration_test_exec_settings):
            subarray = SubArray(subarray_id)
            subarray.release()


@then("the script completes successfully")
def check_script_completed():
    """
    Check that the script that was last run has completed successfully.
    """
    script = EXECUTOR.get_latest_script()
    assert (
        script.state == "COMPLETE"
    ), f"Expected script to be COMPLETED, instead was {script.state}"


@then(parsers.parse("the sub-array goes to ObsState {obsstate}"))
def check_final_subarray_state(
    obsstate: str,
    sut_settings: SutTestSettings,
):
    """
    Check that the final state of the sub-array is as expected.

    :param obsstate: Sub-array Tango device ObsState
    :type obsstate: str
    :param sut_settings: A class representing the settings for the system under test.
    """
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    subarray_state = ObsState(subarray.read_attribute("obsState").value).name
    assert subarray_state == obsstate, (
        f"Expected sub-array to be in {obsstate} but instead was in" f" {subarray_state}"
    )
    logger.info("Sub-array is in ObsState %s", obsstate)


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.scripting
@pytest.mark.skamid
@pytest.mark.k8s

@scenario(
    "features/oet_assign_release_resources.feature",
    "Allocate resources using oet scripting interface",
)
def test_oet__scripting_resource_allocation():
    """
    Given an OET
                And oet subarray object in state EMPTY
                When I assign resources to it
                Then the sub-array goes to ObsState IDLE
    """


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.scripting
@pytest.mark.skalow
@pytest.mark.assign
@pytest.mark.k8s

@scenario(
    "features/oet_assign_release_resources.feature",
    "Allocate resources using oet scripting interface low",
)
def test_oet_scripting_resource_allocation_in_low():
    """
    Given an OET
                And an oet subarray object in state EMPTY
                When I assign resources to it in low
                Then the sub-array goes to ObsState IDLE
    """


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.scripting
@pytest.mark.skalow
@pytest.mark.k8s

@scenario(
    "features/oet_assign_release_resources.feature",
    "Release all resources from sub-array low",
)
def test_resource_release_for_low():
    """
    Given sub-array with resources allocated to it
    When I tell the OET to release resources
    Then the sub-array goes to ObsState EMPTY
    """


@given("an oet subarray object in state EMPTY", target_fixture="subarray")
def an_oet_subarray_object_in_state_empty(
    running_telescope: fxt_types.running_telescope,
    sut_settings: SutTestSettings,
) -> SubArray:
    """
    an oet subarray in empty state
    :param running_telescope: A fixture for running telescope
    :param sut_settings: A class representing the settings for the system under test.
    :return: a subarray with input as subarray id
    """
    return SubArray(sut_settings.subarray_id)


@when("I assign resources to it")
def i_assign_resources_to_it(
    running_telescope: fxt_types.running_telescope,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
    subarray: SubArray,
):
    """
    I assign resources to it.

    :param running_telescope: the running telescope object
    :param context_monitoring: context monitoring object
    :param integration_test_exec_settings: integration test execution settings object
    :param sut_settings: A class representing the settings for the system under test.
    :param subarray: the subarray object to assign resources to subarray
    """

    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors
    observation = sut_settings.observation
    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):
            config = observation.generate_assign_resources_config(subarray_id).as_object
            logging.info(f"eb id from test config:{config.sdp_config.eb_id}")
            subarray.assign_from_cdm(config)


@when("I assign resources to it in low")
def i_assign_resources_to_it_low(
    running_telescope: fxt_types.running_telescope,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
    subarray: SubArray,
):
    """
    I assign resources to it in low.

    :param running_telescope: the running telescope object
    :param context_monitoring: context monitoring object
    :param integration_test_exec_settings: integration test execution settings object
    :param sut_settings: A class representing the settings for the system under test.
    :param subarray: the subarray object to assign resources to subarray
    """

    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors
    observation = sut_settings.observation
    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):
            config = observation.generate_low_assign_resources_config(subarray_id).as_object
            logging.info(f"eb id from test config:{config.sdp_config.eb_id}")
            subarray.assign_from_cdm(config)


@then("the sub-array goes to ObsState IDLE")
def the_subarray_must_be_in_idle_state(sut_settings: SutTestSettings):
    """
    the subarray must be in IDLE state.
    :param sut_settings: A class representing the settings for the system under test.

    """
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)
