import pytest
from pytest_bdd import given, scenario, then, when, parsers

from .oet_helpers import ScriptExecutor
from ska_oso_oet_client.activityclient import ActivityAdapter
from os import environ
kube_namespace = environ.get("KUBE_NAMESPACE", "test")
kube_host = environ.get("KUBE_HOST")
rest_cli_uri = f"http://{kube_host}/{kube_namespace}/api/v1.0"
activity_adapter = ActivityAdapter(f"{rest_cli_uri}/activities")

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
        "I tell the OET to allocate resources for SBI {sbd_id}"
    )
)
def when_allocate_resources_from_activity(
    sbd_id,
):
    """
    """

    activity_adapter.run(
        "allocate",
        sbd_id,
    )
    summaries = activity_adapter.list()
    assert ( summaries[0].state == "REQUESTED" ),\
        f"Expected resource allocation script to be COMPLETED, instead was {summaries[0].state}"

@then("script execution completes successfully")
def hello_world_script_complete():
    "script execution completes successfully"
    latest_task = EXECUTOR.get_latest_script()

    assert latest_task
    assert latest_task.state == "COMPLETE"
