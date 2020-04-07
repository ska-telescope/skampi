import logging
from tango import DevState
from resources.test_support.helpers import resource, watch
import pytest
from time import sleep


@pytest.mark.xfail(reason="subarray node is not in sync with cspsuarray state.")
def test_check_subarray_state_change_sequence(create_centralnode_proxy, create_subarray1_proxy,
                                              create_cspsubarray1_proxy, create_sdpsubarray1_proxy):
    create_centralnode_proxy.StartUpTelescope()

    watch_subarray1_state = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State")
    subarray1_state = watch_subarray1_state.get_value_when_changed()

    if subarray1_state == "OFF":
        assign_res_test_input = '{"subarrayID":1,"dish":{"receptorIDList":["0001","0002"]}}'
        create_centralnode_proxy.AssignResources(assign_res_test_input)

        watch_subarray1_state = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State")
        subarray1_state = watch_subarray1_state.get_value_when_changed()

        if subarray1_state == "ON":
            release_res_test_input = '{"subarrayID":1,"releaseALL":true,"receptorIDList":[]}'
            create_centralnode_proxy.ReleaseResources(release_res_test_input)
            # When ReleaseResources command is invoked, subarraynode should change its state to "OFF"
            # *after* cspsubarray and sdpsubarray change their state to "OFF"
            logging.info("cspsubarray1 state: " + resource('mid_csp/elt/subarray_01').get("State"))
            logging.info("sdpsubarray1 state: " + resource('mid_sdp/elt/subarray_1').get("State"))
            logging.info("subarray1 state: " + resource('ska_mid/tm_subarray_node/1').get("State"))

            assert ((create_cspsubarray1_proxy.state() == DevState.OFF or
                     create_sdpsubarray1_proxy.state() == DevState.OFF) and
                    create_subarray1_proxy.state() == DevState.ON)

            watch_cspsubarray1_state = watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("State")
            cspsubarray1_state = watch_cspsubarray1_state.get_value_when_changed()

            logging.info("cspsubarray1 state: " + resource('mid_csp/elt/subarray_01').get("State"))
            logging.info("sdpsubarray1 state: " + resource('mid_sdp/elt/subarray_1').get("State"))
            logging.info("subarray1 state: " + resource('ska_mid/tm_subarray_node/1').get("State"))

            if cspsubarray1_state == "OFF":
                assert ((create_cspsubarray1_proxy.state() == DevState.OFF or
                         create_sdpsubarray1_proxy.state() == DevState.OFF) and
                        create_subarray1_proxy.state() == DevState.OFF)

    create_centralnode_proxy.StandByTelescope()
    sleep(3)
