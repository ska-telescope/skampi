from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types


def setup_csp_mock(mock_entry_point: fxt_types.mock_entry_point):
    @mock_entry_point.when_set_telescope_to_running
    def mck_set_telescope_to_running():
        mock_entry_point.model.csp.set_states_for_telescope_running()

    @mock_entry_point.when_set_telescope_to_standby
    def mck_set_telescope_to_standby():
        mock_entry_point.model.csp.set_states_for_telescope_standby()
