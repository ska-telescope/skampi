import logging
import os
import time
from typing import Callable
from mock import patch, Mock

import pytest
from pipe import select, where
from resources.models.cbf_model.entry_point import CBFEntryPoint
from resources.models.cbf_model.mocking import setup_cbf_mock
from resources.models.csp_model.entry_point import CSPEntryPoint
from resources.models.csp_model.mocking import setup_csp_mock
from resources.models.mccs_model.entry_point import MCCSEntryPoint
from resources.models.sdp_model.entry_point import SDPEntryPoint
from resources.models.sdp_model.mocking import setup_sdp_mock
from resources.models.mvp_model.session_entry_point import get_session_entry_point
from ska_ser_skallop.connectors.tangodb import TangoDB
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types


logger = logging.getLogger(__name__)

MOCK_SUT = False
NR_OFF_SUBARRAYS = 2


@pytest.fixture(scope="session", autouse=True)
def fxt_check_tango_db(request):
    # pylint: disable=no-value-for-parameter
    if not os.getenv("DEVENV"):
        db = TangoDB()
        devices = "\n".join(db.devices | where(lambda args: "dserver/" not in args[0]))
        logger.info("#### Devices and States ####")
        logger.info(
            f"\n\x1b[0Ksection_start:{int(time.time())}:devices[collapsed=true]\r\x1b[0KDevices in db:"
        )
        logger.info(f"{devices}")
        logger.info(f"\n\x1b[0Ksection_end:{int(time.time())}:devices\r\x1b[0K")

        device_states = list(db.get_db_state().items())
        device_states = "\n".join(
            device_states
            | where(lambda args: "dserver/" not in args[0])
            | select(lambda args: f"{args[0]:<100}{args[1]}")
        )
        logger.info(
            f"\n\x1b[0Ksection_start:{int(time.time())}:device_states[collapsed=true]\r\x1b[0KDevice states:"
        )
        logger.info(f"{device_states}")
        logger.info(f"\n\x1b[0Ksection_end:{int(time.time())}:device_states\r\x1b[0K")


@pytest.fixture(autouse=True, scope="session")
def fxt_set_session_entry_point(set_session_exec_env: fxt_types.set_session_exec_env):
    if not os.getenv("DEVENV"):
        env = set_session_exec_env
        env.session_entry_point = get_session_entry_point()


@pytest.fixture(name="run_mock")
def fxt_run_mock_wrapper(request, _pytest_bdd_example):
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
    exec_env = set_session_exec_env
    if not MOCK_SUT:
        SDPEntryPoint.nr_of_subarrays = NR_OFF_SUBARRAYS
        exec_env.entrypoint = SDPEntryPoint
    else:
        exec_env.entrypoint = "mock"
    exec_env.scope = ["sdp"]


@pytest.fixture(name="set_csp_entry_point")
def fxt_set_csp_entry_point(
    set_session_exec_env: fxt_types.set_session_exec_env,
    exec_settings: fxt_types.exec_settings,
):
    exec_env = set_session_exec_env
    exec_settings.time_out = 20
    if not MOCK_SUT:
        CSPEntryPoint.nr_of_subarrays = NR_OFF_SUBARRAYS
        exec_env.entrypoint = CSPEntryPoint
    else:
        exec_env.entrypoint = "mock"
    exec_env.scope = ["csp"]


@pytest.fixture(name="set_cbf_entry_point")
def fxt_set_cbf_entry_point(
    set_session_exec_env: fxt_types.set_session_exec_env,
    exec_settings: fxt_types.exec_settings,
):
    exec_env = set_session_exec_env
    exec_settings.time_out = 20
    if not MOCK_SUT:
        CBFEntryPoint.nr_of_subarrays = NR_OFF_SUBARRAYS
        exec_env.entrypoint = CBFEntryPoint
    else:
        exec_env.entrypoint = "mock"
    # include csp in scope when deployed
    if exec_env.telescope_type == "skalow":
        exec_env.scope = ["cbf scope", "csp controller"]
    else:
        exec_env.scope = ["cbf scope"]


@pytest.fixture(name="set_mccs_entry_point")
def fxt_set_mssc_entry_point(
    set_session_exec_env: fxt_types.set_session_exec_env,
    exec_settings: fxt_types.exec_settings,
):
    exec_env = set_session_exec_env
    exec_settings.time_out = 20
    if not MOCK_SUT:
        MCCSEntryPoint.nr_of_subarrays = NR_OFF_SUBARRAYS
        exec_env.entrypoint = MCCSEntryPoint
    else:
        exec_env.entrypoint = "mock"
    exec_env.scope = ["mccs"]


@pytest.fixture(name="setup_sdp_mock")
def fxt_setup_sdp_mock(mock_entry_point: fxt_types.mock_entry_point):
    setup_sdp_mock(mock_entry_point)


@pytest.fixture(name="setup_csp_mock")
def fxt_setup_csp_mock(mock_entry_point: fxt_types.mock_entry_point):
    setup_csp_mock(mock_entry_point)


@pytest.fixture(name="setup_cbf_mock")
def fxt_setup_cbf_mock(mock_entry_point: fxt_types.mock_entry_point):
    setup_cbf_mock(mock_entry_point)
