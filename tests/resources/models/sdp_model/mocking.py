"""Module containg mock implementation of an entrypoint for SDP."""
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from .entry_point import SDPEntryPoint


def setup_sdp_mock(mock_entry_point: fxt_types.mock_entry_point):
    """function that updates the mock_entry_point in the context of SDP.

    :param mock_entry_point: _description_
    :type mock_entry_point: fxt_types.mock_entry_point
    """
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
        elif subarray_id == 2:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.RESOURCING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.IDLE)
            )
        elif subarray_id == 3:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.RESOURCING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.IDLE)
            )
        elif subarray_id == 4:
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
        elif subarray_id == 2:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.RESOURCING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.EMPTY)
            )
        elif subarray_id == 3:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.RESOURCING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.EMPTY)
            )
        elif subarray_id == 4:
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
        elif subarray_id == 2:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.CONFIGURING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.READY)
            )
        elif subarray_id == 3:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.CONFIGURING)
            )
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.READY)
            )
        elif subarray_id == 4:
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
        elif subarray_id == 2:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.IDLE)
            )
        elif subarray_id == 3:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.IDLE)
            )
        elif subarray_id == 4:
            mock_entry_point.model.sdp.subarray1.set_attribute(
                "obsstate", ObsState(ObsState.IDLE)
            )
