"""Default feature tests."""
import os
from ska_ser_skallop.connectors.configuration import get_device_proxy
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@scenario("features/tangogql_upload.feature", "TangoGQL service available")
def test_tangojql_service_available():
    """TangoGql service available."""


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


@then("I expect a response to be returned from the device server")
def i_expect_a_response_to_be_returned_from_the_device_server():
    """I expect a response to be returned from the device server."""
