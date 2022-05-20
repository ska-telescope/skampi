"""Pytest fixtures and BDD step implementations specific to OET integration tests."""
import logging

import pytest
from pytest_bdd import given, scenario, then, when

from .oet_helpers import ScriptExecutor

LOGGER = logging.getLogger(__name__)

EXECUTOR = ScriptExecutor()

@pytest.mark.skamid
@pytest.mark.k8s
@scenario("features/oet_basic.feature", "Run the hello_world test script")
def test_telescope_startup_mid():
    """Telescope startup test."""

@given("The OET is integrated with SKAMPI")
def hello_world_script_created():
    pass


@when("the script is ran")
def hello_world_script_ran():
    EXECUTOR.execute_script("file:///data/hello_world.py")


@then("script execution completes successfully")
def hello_world_script_complete():
    latest_task = EXECUTOR.get_latest_script()

    assert latest_task.state == 'COMPLETE'

