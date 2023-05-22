"""Cucumber test results are uploaded to XRay feature tests."""

import json
import os
from asyncio.log import logger

import pytest
from atlassian import Jira
from pytest_bdd import given, scenario, then, when

# declare pytestmark globally so that the whole scenario can be marked as infra
pytestmark = pytest.mark.infra


@scenario(
    "features/xray_upload.feature",
    "SKAMPI CI Pipeline tests execute on SKAMPI",
)
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


@scenario(
    "features/xray_upload.feature",
    "Test if test-exec.json is configured to the latest Unreleased Version",
)
def test_fix_version_is_correct():
    """SKAMPI CI Pipeline tests execute on SKAMPI."""


@given(
    (
        "the SKA Jira project for Solution and System Acceptance Tests (skampi"
        " tests) with project key XTP"
    ),
    target_fixture="unreleased_fixversion",
)
def get_earliest_unreleased_fix_version():
    """Get the earliest unreleased FixVersion in Jira project

    :return: FixVersion is defined according to PIs
    :rtype: str
    """
    url = os.environ["JIRA_URL"]
    username = os.environ["JIRA_USERNAME"]
    password = os.environ["JIRA_PASSWORD"]
    jira = Jira(url=url, username=username, password=password)
    project_key = "XTP"
    versions = jira.get_project_versions(key=project_key, expand="All")
    unrel_vs = [v for v in versions if v["released"] is False]
    filtered_vs = [v for v in unrel_vs if v["archived"] is False][0]
    logger.info(f"{filtered_vs}")
    return filtered_vs["name"]


@given(
    "a test-exec.json file that contains a version parameter",
    target_fixture="local_version",
)
def fxt_load_file():
    """Extract Fix Version in local config

    :return: Current PI that all uploads will be associated with
    :rtype: str
    """
    fn = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), os.path.pardir, "test-exec.json"
        )
    )
    with open(
        fn,
        "rb",
    ) as file:
        data = json.load(file)
        curr_pi = data["versions"][0]["maps_to"]["master"]
    logger.info(f"Local FixVersion set to {curr_pi}")
    return curr_pi


@when(
    "integration tests are uploaded after tests executed in Skampi master"
    " branch pipelines"
)
def get_fix_version_from_test_exec_json_file():
    """This step will happen after all the tests were executed"""


@then(
    "the results will be associated with the Earliest Unreleased FixVersion in"
    " the XTP project"
)
def check_if_fix_version_matches(
    local_version: str, unreleased_fixversion: str
):
    """Test to see if they matched

    :param unreleased_fixversion: fixture
    :type unreleased_fixversion: str
    :param local_version: fixture
    :type local_version: str
    """
    assert local_version == unreleased_fixversion, (
        f"{local_version} in test-exec.json; earliest unreleased version in"
        f" Jira: {unreleased_fixversion}"
    )
