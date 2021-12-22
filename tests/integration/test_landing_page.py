"""Landing Page Availability and link generation feature tests."""

import os
from typing import NamedTuple

import pytest
import requests
from assertpy.assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from requests.models import Response


class ENV(NamedTuple):
    host: str
    namespace: str


@pytest.fixture(name="env")
def fxt_env() -> ENV:
    host = os.getenv("KUBE_HOST")
    assert host, "Unable to continue with test as KUBE_HOST is not set"
    namespace = os.getenv("KUBE_NAMESPACE")
    assert namespace, "Unable to continue with test as KUBE_NAMESPACE is not set"
    return ENV(host, namespace)


@pytest.mark.skalow
@scenario("features/landing_page.feature", "Test landing page available on ska low")
def test_test_landing_page_available_on_ska_low():
    """Test landing page available on ska low."""


@pytest.mark.skamid
@scenario("features/landing_page.feature", "Test landing page available on ska mid")
def test_test_landing_page_available_on_ska_mid():
    """Test landing page available on ska mid."""


@given("a deployed ska-mid", target_fixture="base_url")
@given("a deployed ska-low", target_fixture="base_url")
def a_deployed_skalow(env: ENV):
    """a deployed ska-low."""
    return f"http://{env.host}/{env.namespace}/start/"


@when("I access the landing page url in the browser", target_fixture="http_response")
def i_access_the_landing_page_url_in_the_browser(base_url: str) -> Response:
    """I access the landing page url in the browser."""
    return requests.get(base_url)


@then("the landing page is rendered correctly")
def the_landing_page_is_rendered_correctly(http_response: Response):
    """the landing page is rendered correctly."""
    assert_that(http_response.status_code).is_equal_to(200)
