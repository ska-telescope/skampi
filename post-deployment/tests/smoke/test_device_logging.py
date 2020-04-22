from resources.test_support.helpers import device_logging
import logging
import json


   
def test_device_logging():
    d = device_logging()
    d.update_traces(['ska_mid/tm_subarray_node/1'])
    #logging.debug("the device target = {}",str(d.tracer.dev))
    d.start_tracing()
    logging.info(d.get_printable_messages(wait=True))
    d.stop_tracing()

    
