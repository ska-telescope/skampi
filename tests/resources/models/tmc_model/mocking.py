from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from .entry_point import TMCEntryPoint


def setup_tmc_mock(mock_entry_point: fxt_types.mock_entry_point):
    mock_entry_point.set_spy(TMCEntryPoint)
