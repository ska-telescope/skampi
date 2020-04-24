from resources.test_support.helpers import DeviceLogging
import logging
import json
import pytest
from time import sleep

@pytest.mark.tracer
def test_device_logging():
    d = DeviceLogging()
    d.update_traces(['sys/tg_test/1'])
    #logging.debug("the device target = {}",str(d.tracer.dev))
    logging.info('starting traces for sys/tg_test/1')
    d.start_tracing()
    d.wait_until_message_received("DataGenerator::generating data", 20)
    logging.info(d.get_printable_messages())
    d.stop_tracing()
    d = DeviceLogging()
    d.update_traces(['mid_csp/elt/subarray_01'])
    logging.info('starting traces for mid_csp/elt/subarray_01')
    d.start_tracing()
    sleep(5)
    logging.info(d.get_printable_messages())
    d.stop_tracing()


    
