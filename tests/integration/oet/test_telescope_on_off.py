from pytest_bdd import given, scenario, then
import pytest


@pytest.mark.skamid
@scenario("features/oet_turn_on.feature", "Run the hello_world test script")
def test_run_hello_world_script():
    """Run a hello_world script from the OET"""
