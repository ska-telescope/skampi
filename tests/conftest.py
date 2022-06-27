# pylint: disable=unused-argument
import logging
import socket

import pytest
# from kubernetes import client, config, watch

# import tango
# from tango.test_context import MultiDeviceTestContext, get_host_ip

# from ska_tango_examples.DevFactory import DevFactory

# def pytest_sessionstart(session):
#     """
#     Pytest hook; prints info about tango version.
#     :param session: a pytest Session object
#     :type session: :py:class:`pytest.Session`
#     """
#     print(tango.utils.info())


def pytest_addoption(parser):
    """
    Pytest hook; implemented to add the `--true-context` option, used to
    indicate that a true Tango subsystem is available, so there is no
    need for a :py:class:`tango.test_context.MultiDeviceTestContext`.
    :param parser: the command line options parser
    :type parser: :py:class:`argparse.ArgumentParser`
    """
    parser.addoption(
        "--true-context",
        action="store_true",
        default=False,
        help=(
            "Tell pytest that you have a true Tango context and don't "
            "need to spin up a Tango test context"
        ),
    )


# uncomment this if you want to override the default timeout settings in case your environment entails very long delays
@pytest.fixture(autouse=True)
def override_timeouts(exec_settings):
exec_settings.time_out = 200

# @pytest.fixture
# def tango_context(devices_to_load, request):
#     true_context = request.config.getoption("--true-context")
#     logging.info("true context: %s", true_context)
#     if not true_context:
#         with MultiDeviceTestContext(devices_to_load, process=False) as context:
#             DevFactory._test_context = context
#             yield context
#     else:
#         yield None


# @pytest.fixture(scope="module")
# def devices_to_test(request):
#     yield getattr(request.module, "devices_to_test")


# @pytest.fixture(scope="function")
# def multi_device_tango_context(
#     mocker, devices_to_test  # pylint: disable=redefined-outer-name
# ):
#     """
#     Creates and returns a TANGO MultiDeviceTestContext object, with
#     tango.DeviceProxy patched to work around a name-resolving issue.
#     """

#     def _get_open_port():
#         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         s.bind(("", 0))
#         s.listen(1)
#         port = s.getsockname()[1]
#         s.close()
#         return port

#     HOST = get_host_ip()
#     PORT = _get_open_port()
#     _DeviceProxy = tango.DeviceProxy
#     mocker.patch(
#         "tango.DeviceProxy",
#         wraps=lambda fqdn, *args, **kwargs: _DeviceProxy(
#             "tango://{0}:{1}/{2}#dbase=no".format(HOST, PORT, fqdn),
#             *args,
#             **kwargs
#         ),
#     )
#     with MultiDeviceTestContext(
#         devices_to_test, host=HOST, port=PORT, process=True
#     ) as context:
#         yield context
