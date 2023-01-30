import pytest
from pytest_bdd import given, scenario, then, when, parsers

from .oet_helpers import ScriptExecutor, ACTIVITY_ADAPTER
from os import environ

EXECUTOR = ScriptExecutor()

@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.k8s
@scenario("features/oet_basic.feature", "Run the hello_world test script")
def test_hello_world():
    """Telescope startup test."""

@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.k8s
@scenario("features/oet_basic.feature", "Run the hello_world test script via an SB activity")
def test_activity():
    """."""


@given("The OET is integrated with SKAMPI")
def hello_world_script_created():
    "The OET is integrated with SKAMPI"


@when("the script is ran")
def hello_world_script_ran():
    EXECUTOR.execute_script("file:///tmp/oda/hello_world.py")

@when(
    parsers.parse(
        "I tell the OET to run {activity_name} activity for SBI {sbd_id}"
    )
)
def when_allocate_resources_from_activity(
    activity_name,
    sbd_id,
):
    """
    """
    ACTIVITY_ADAPTER.run(
        allocate,
        sbd_id,
    )
    assert ( summaries[0].state == "REQUESTED" ),\
        f"Expected resource allocation script to be COMPLETED, instead was {summaries[0].state}"

@then("script started by the activity completes successfully")
def hello_world_script_complete():
    "script execution completes successfully"

    summaries = ACTIVITY_ADAPTER.list()
    pid = summaries[0].procedure_id
    procedure_status = EXECUTOR.wait_for_script_state(pid, "COMPLETE", timeout=20)

    assert procedure_status == "COMPLETE"

@then("script execution completes successfully")
def hello_world_script_complete():
    "script execution completes successfully"
    procedure = EXECUTOR.get_latest_script()

    assert procedure.state == "COMPLETE"
