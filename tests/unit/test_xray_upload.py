"""Cucumber test results are uploaded to XRay feature tests."""

import pytest
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)

# declare pytestmark globally so that the whole scenario can be marked as infra
pytestmark = pytest.mark.infra


@scenario("features/xray_upload.feature", "SKAMPI CI Pipeline tests execute on SKAMPI")
def test_skampi_ci_pipeline_tests_execute_on_skampi():
    """SKAMPI CI Pipeline tests execute on SKAMPI."""


@given("a Continuous Integration Pipeline")
def stuff():
    """a Continuous Integration Pipeline."""
    pass


@when("an attempt is made to run tests within the repository")
def stuff_happens():
    """an attempt is made to run tests within the repository."""
    pass


@then("the tests within the SKAMPI repository are run")
def all_is_good():
    """the tests within the SKAMPI repository are run."""
    pass
