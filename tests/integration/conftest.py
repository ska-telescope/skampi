from typing import Callable

import pytest
from resources.models.cbf_model.entry_point import CBFEntryPoint
from resources.models.csp_model.entry_point import CSPEntryPoint
from resources.models.sdp_model.entry_point import SDPEntryPoint
from resources.models.sdp_model.mocking import setup_sdp_mock
from resources.models.cbf_model.mocking import setup_cbf_mock
from resources.models.csp_model.mocking import setup_csp_mock
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

MOCK_SUT = False
NR_OFF_SUBARRAYS = 2


@pytest.fixture(name="run_mock")
def fxt_run_mock_wrapper(request, _pytest_bdd_example):
    def run_mock(mock_test: Callable):
        """Test the test using a mock SUT"""
        global MOCK_SUT  # pylint: disable=global-statement
        MOCK_SUT = True
        # pylint: disable-next=too-many-function-args
        mock_test(request, _pytest_bdd_example)  # type: ignore

    return run_mock


@pytest.fixture(name="set_sdp_entry_point", scope="session")
def fxt_set_entry_point(set_session_exec_env: fxt_types.set_session_exec_env):
    exec_env = set_session_exec_env
    if not MOCK_SUT:
        SDPEntryPoint.nr_of_subarrays = NR_OFF_SUBARRAYS
        exec_env.entrypoint = SDPEntryPoint
        exec_env.session_entry_point = SDPEntryPoint
    else:
        exec_env.entrypoint = "mock"
    exec_env.scope = ["sdp"]


@pytest.fixture(name="set_csp_entry_point", scope="session")
def fxt_set_csp_entry_point(set_session_exec_env: fxt_types.set_session_exec_env):
    exec_env = set_session_exec_env
    if not MOCK_SUT:
        CSPEntryPoint.nr_of_subarrays = NR_OFF_SUBARRAYS
        exec_env.entrypoint = CSPEntryPoint
        exec_env.session_entry_point = CSPEntryPoint
    else:
        exec_env.entrypoint = "mock"
    exec_env.scope = ["csp"]


@pytest.fixture(name="set_cbf_entry_point", scope="session")
def fxt_set_cbf_entry_point(set_session_exec_env: fxt_types.set_session_exec_env):
    exec_env = set_session_exec_env
    if not MOCK_SUT:
        CBFEntryPoint.nr_of_subarrays = NR_OFF_SUBARRAYS
        exec_env.entrypoint = CBFEntryPoint
        exec_env.session_entry_point = CBFEntryPoint
    else:
        exec_env.entrypoint = "mock"
    exec_env.scope = ["cbf scope"]


@pytest.fixture(name="setup_sdp_mock")
def fxt_setup_sdp_mock(mock_entry_point: fxt_types.mock_entry_point):
    setup_sdp_mock(mock_entry_point)


@pytest.fixture(name="setup_csp_mock")
def fxt_setup_csp_mock(mock_entry_point: fxt_types.mock_entry_point):
    setup_csp_mock(mock_entry_point)


@pytest.fixture(name="setup_cbf_mock")
def fxt_setup_cbf_mock(mock_entry_point: fxt_types.mock_entry_point):
    setup_cbf_mock(mock_entry_point)
