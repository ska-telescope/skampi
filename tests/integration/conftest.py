import logging

from typing import Callable
from mock import patch, Mock

import pytest


from resources.models.sdp_model.entry_point import SDPEntryPoint
from resources.models.sdp_model.mocking import setup_sdp_mock
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types


logger = logging.getLogger(__name__)

MOCK_SUT = False
NR_OFF_SUBARRAYS = 2


@pytest.fixture(name="run_mock")
def fxt_run_mock_wrapper(request, _pytest_bdd_example):
    """Fixture that returns a function to use for running a test as a mock."""

    def run_mock(mock_test: Callable):
        """Test the test using a mock SUT"""
        global MOCK_SUT  # pylint: disable=global-statement
        MOCK_SUT = True
        # pylint: disable-next=too-many-function-args
        with patch(
            "ska_ser_skallop.mvp_fixtures.fixtures.TransitChecking"
        ) as transit_checking_mock:
            transit_checking_mock.return_value.checker = Mock(unsafe=True)
            mock_test(request, _pytest_bdd_example)  # type: ignore

    return run_mock


@pytest.fixture(name="set_sdp_entry_point")
def fxt_set_entry_point(set_session_exec_env: fxt_types.set_session_exec_env):
    """Fixture to use for setting up the entry point as from only the interface to sdp."""
    exec_env = set_session_exec_env
    if not MOCK_SUT:
        SDPEntryPoint.nr_of_subarrays = NR_OFF_SUBARRAYS
        exec_env.entrypoint = SDPEntryPoint
    else:
        exec_env.entrypoint = "mock"
    exec_env.scope = ["sdp"]


@pytest.fixture(name="setup_sdp_mock")
def fxt_setup_sdp_mock(mock_entry_point: fxt_types.mock_entry_point):
    """Fixture to use for injecting a mocked entrypoin for sdp in stead of the real one."""
    setup_sdp_mock(mock_entry_point)
