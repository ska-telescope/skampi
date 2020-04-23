from resources.test_support.helpers import device_logging
import logging
import json
from time import sleep


def test_device_logging():
    d = device_logging()
    d.update_traces(['sys/tg_test/1'])
    #logging.debug("the device target = {}",str(d.tracer.dev))
    logging.info('starting traces for sys/tg_test/1')
    d.start_tracing()
    logging.info(d.get_printable_messages(wait=True))
    d.stop_tracing()
    d = device_logging()
    d.update_traces(['mid_csp/elt/subarray_01'])
    logging.info('starting traces for mid_csp/elt/subarray_01')
    d.start_tracing()
    sleep(5)
    logging.info(d.get_printable_messages())
    d.stop_tracing()


    
