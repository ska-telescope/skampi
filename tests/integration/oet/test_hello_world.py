import pytest
from pytest_bdd import given, scenario, then, when, parsers

from ska_db_oda.unit_of_work.restunitofwork import RESTUnitOfWork

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


@given(
    parsers.parse(
        "SB with id {sb_id} and activity {activity_name} exists in ODA"
    )
)
def hello_world_sb_in_oda(sb_id, activity_name, test_sbd):
    ""
    oda = RESTUnitOfWork()
    test_sbd.sbd_id = sb_id

    assert activity_name in test_sbd.activities, \
        f"Activity test setup failed, no activity called {activity_name} in test SB"

    with oda:
        try:
            existing_sbd = oda.sbds.get(test_sbd.sbd_id)
            test_sbd.metadata.version = existing_sbd.metadata.version
        except KeyError:
            # sbd_id doesn't exist in ODA so no need to worry about versions
            pass
        oda.sbds.add(test_sbd)
        oda.commit()


@when("the script is ran")
def hello_world_script_ran():
    EXECUTOR.execute_script("file:///tmp/oda/hello_world.py")

@when(
    parsers.parse(
        "I tell the OET to run {activity_name} activity for SBI {sb_id}"
    )
)
def when_allocate_resources_from_activity(
    activity_name,
    sb_id,
):
    """
    """
    ACTIVITY_ADAPTER.run(
        activity_name,
        sb_id,
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
