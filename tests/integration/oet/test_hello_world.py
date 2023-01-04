import pytest
from pytest_bdd import given, scenario, then, when

from .oet_helpers import ScriptExecutor

EXECUTOR = ScriptExecutor()

@pytest.mark.oet
## @pytest.mark.skamid
@pytest.mark.k8s
@scenario("features/oet_basic.feature", "Run the hello_world test script")
def test_hello_world():
    """Telescope startup test."""


@given("The OET is integrated with SKAMPI")
def hello_world_script_created():
    "The OET is integrated with SKAMPI"


@when("the script is ran")
def hello_world_script_ran():
    EXECUTOR.execute_script("file:///tmp/oda/hello_world.py")


@then("script execution completes successfully")
def hello_world_script_complete():
    "script execution completes successfully"
    latest_task = EXECUTOR.get_latest_script()

    assert latest_task
    assert latest_task.state == "COMPLETE"
