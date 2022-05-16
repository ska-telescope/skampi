import pytest
from pytest_bdd import given, scenario, then


@pytest.mark.skamid
@scenario("features/oet_start_up_telescope.feature", "Run the hello_world test script")
def test_run_hello_world_script():
    """Run a hello_world script from the OET"""
