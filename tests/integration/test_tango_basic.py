"""Default feature tests."""
import os
from typing import NamedTuple
from assertpy.assertpy import assert_that

import requests
import pytest
from pytest_bdd import given, scenario, then, when
from requests.models import Response
from assertpy import assert_that
from ska_ser_skallop.connectors.configuration import get_device_proxy


@scenario("features/taranta_basic.feature", "TangoGQL service available")
def test_tangogql_service_available():
    """TangoGQL service available."""


@given("a configuration to access a tango device remotely")
def a_configuration_to_access_a_tango_device_remotely():
    """a configuration to access a tango device remotely."""
    os.environ["TEST_ENV"] = "BUILD_OUT"


@when("I send a ping command to the tango database device server")
def i_send_a_ping_command_to_the_tango_database_device_server():
    """I send a ping command to the tango database device server."""
    device_name = "sys/database/2"
    device_proxy = get_device_proxy(device_name)
    device_proxy.ping()


@pytest.mark.taranta
@then("I expect a response to be returned from the device server")
def i_expect_a_response_to_be_returned_from_the_device_server():
    """I expect a response to be returned from the device server."""


@pytest.mark.taranta
@scenario("features/taranta_basic.feature", "taranta dashboard services available")
def test_taranta_dashboard_services_available():
    """taranta dashboard services available."""


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


@given("a deployed Taranta web dashboard service", target_fixture="service_url")
def a_deployed_taranta_web_dashboard_service(env: ENV) -> str:
    """a deployed Taranta web dashboard service."""
    return f"http://{env.host}/{env.namespace}/taranta/dashboard/"


@pytest.mark.taranta
@scenario("features/taranta_basic.feature", "taranta devices service available")
def test_taranta_devices_service_available(env: ENV) -> str:
    """taranta devices service available."""


@given("a deployed Taranta web devices service", target_fixture="service_url")
def a_deployed_taranta_web_devices_service(env: ENV):
    """a deployed Taranta web devices service."""
    return f"http://{env.host}/{env.namespace}/taranta/devices/"


@when("I call its REST url", target_fixture="http_response")
def i_call_its_rest_url(service_url: str) -> Response:
    """I call its REST url."""
    return requests.get(service_url)


@then("I get a valid response")
def i_get_a_valid_response(http_response: Response):
    """I get a valid response."""
    assert_that(http_response.status_code).is_equal_to(200)
