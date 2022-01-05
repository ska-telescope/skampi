from typing import Callable
import pytest

from resources.models.sdp_model.entry_point import SDPEntryPoint
from resources.models.csp_model.entry_point import CSPEntryPoint
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.configuration import composition as comp
from resources.models.mvp_model.states import ObsState


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


@pytest.fixture(name="setup_sdp_mock")
def fxt_setup_sdp_mock(mock_entry_point: fxt_types.mock_entry_point):
    mock_entry_point.set_spy(SDPEntryPoint)

    @mock_entry_point.when_set_telescope_to_running
    def mck_set_telescope_to_running():
        mock_entry_point.model.sdp.set_states_for_telescope_running()

    @mock_entry_point.when_set_telescope_to_standby
    def mock_set_telescope_to_standby():
        mock_entry_point.model.sdp.set_states_for_telescope_standby()

    @mock_entry_point.when_compose_subarray
    def mock_compose_subarray(
        subarray_id: int,
        _: list[int],
        __: conf_types.Composition,
        ___: str,
    ):
        if subarray_id == 1:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.RESOURCING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.IDLE)
            )
        if subarray_id == 2:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.RESOURCING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.IDLE)
            )
        if subarray_id == 3:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.RESOURCING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.IDLE)
            )
        if subarray_id == 4:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.RESOURCING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.IDLE)
            )

    @mock_entry_point.when_tear_down_subarray
    def mock_tear_down_subarray(subarray_id: int):
        if subarray_id == 1:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.RESOURCING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.EMPTY)
            )
        if subarray_id == 2:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.RESOURCING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.EMPTY)
            )
        if subarray_id == 3:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.RESOURCING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.EMPTY)
            )
        if subarray_id == 4:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.RESOURCING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.EMPTY)
            )

    @mock_entry_point.when_configure_subarray
    def mock_configure_subarray(
        subarray_id: int,
        _: list[int],
        __: conf_types.ScanConfiguration,
        ___: str,
        ____: float,
    ):
        if subarray_id == 1:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.CONFIGURING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.READY)
            )
        if subarray_id == 2:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.CONFIGURING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.READY)
            )
        if subarray_id == 3:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.CONFIGURING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.READY)
            )
        if subarray_id == 4:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.CONFIGURING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.READY)
            )

    @mock_entry_point.when_clear_configuration
    def mock_clear_configuration(subarray_id: int):
        if subarray_id == 1:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.IDLE)
            )
        if subarray_id == 2:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.IDLE)
            )
        if subarray_id == 3:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.IDLE)
            )
        if subarray_id == 4:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.IDLE)
            )
