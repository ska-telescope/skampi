import pytest
from pytest_bdd import given, parsers, scenario, then, when

from .oet_helpers import ACTIVITY_ADAPTER, ScriptExecutor, add_sb_to_oda

EXECUTOR = ScriptExecutor()


@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.k8s
@scenario("features/oet_basic.feature", "Run the hello_world test script")
def test_hello_world():
    """
    Given The OET is integrated with SKAMPI
    When the script is run
    Then script execution completes successfully
    """


@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.k8s
@scenario(
    "features/oet_basic.feature",
    "Run the hello_world test script via an SB activity",
)
def test_activity():
    """
    Given a test SB with activity helloworld exists in ODA
    When I tell the OET to run helloworld activity on the test SB
    Then script started by the activity completes successfully
    """


@given("The OET is integrated with SKAMPI")
def hello_world_script_created():
    "The OET is integrated with SKAMPI"


@given(parsers.parse("a test SB with activity {activity_name} exists in ODA"))
def hello_world_sb_in_oda(activity_name, test_sbd):
    """
    a test SB with activity  exists in ODA
    :param activity_name : activity name which exists in ODA
    :param test_sbd: An object for test_sbd
    """
    assert activity_name in test_sbd.activities, (
        f"Activity test setup failed, no activity called {activity_name} in" " test SB"
    )

    add_sb_to_oda(test_sbd)


@when(parsers.parse("the script {script} is run"))
def hello_world_script_ran(script):
    EXECUTOR.execute_script(script)


@when(parsers.parse("I tell the OET to run {activity_name} activity on the test SB"))
def when_allocate_resources_from_activity(
    activity_name,
    test_sbd,
):
    """
    I tell the OET to run activity on the test SB
    :param activity_name : activity name which exists in ODA
    :param test_sbd: An object for test_sbd
    """
    summary = ACTIVITY_ADAPTER.run(
        activity_name,
        test_sbd.sbd_id,
    )
    assert (
        summary.state == "TODO"
    ), f"Expected activity with status TODO, instead got {summary.state}"


@then("script started by the activity completes successfully")
def hello_world_script_complete_activity():
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
