"""Cucumber test results are uploaded to XRay feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


# @scenario('features/xray_upload.feature', 'An always passing test')
# def test_an_always_passing_test():
#     """An always passing test."""


@scenario('features/xray_upload.feature', 'SKAMPI CI Pipeline tests execute on SKAMPI')
def test_skampi_ci_pipeline_tests_execute_on_skampi():
    """SKAMPI CI Pipeline tests execute on SKAMPI."""


@given('a Continuous Integration Pipeline')
def a_continuous_integration_pipeline():
    """a Continuous Integration Pipeline."""
    pass


@when('an attempt is made to run tests within the repository')
def an_attempt_is_made_to_run_tests_within_the_repository():
    """an attempt is made to run tests within the repository."""
    pass


@then('the tests within the SKAMPI repository are run')
def the_tests_within_the_skampi_repository_are_run():
    """the tests within the SKAMPI repository are run."""
    pass


@then('there was a passing test')
def there_was_a_passing_test():
    """there was a passing test."""
    pass

