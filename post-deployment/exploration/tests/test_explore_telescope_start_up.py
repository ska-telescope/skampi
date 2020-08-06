from tango import DeviceProxy
from resources.test_support.event_waiting import observe_states,sync_telescope_shutting_down,watchSpec,sync_telescope_starting_up
import logging
from time import sleep

LOGGER = logging.getLogger(__name__)
from oet.domain import SKAMid

def test_startup():
    cn = DeviceProxy('ska_mid/tm_central/central_node')
    specs = [
        #watchSpec('ska_mid/tm_subarray_node/1','State'),        
        watchSpec('mid_csp/elt/subarray_01','State'),
        watchSpec('mid_csp_cbf/sub_elt/subarray_01','State'),
        watchSpec('mid_csp/elt/master','State'),
        #watchSpec('ska_mid/tm_central/central_node','State'),   
    ]
    #with observe_states(specs,LOGGER,timeout=2):
     #   cn.StartUpTelescope()
    #with observe_states(specs,LOGGER,timeout=5):
    with sync_telescope_starting_up(LOGGER,timeout=4):
        logging.info('starting up telescope')
        SKAMid().start_up()
    #sleep(1)
    #with observe_states(specs,LOGGER,timeout=5):
    with sync_telescope_shutting_down(LOGGER,timeout=4):
        logging.info('shutting down telescope')
        SKAMid().standby()

