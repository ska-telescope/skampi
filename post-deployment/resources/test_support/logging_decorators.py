import functools
from resources.test_support.state_checking import StateChecker
from resources.test_support.log_helping import DeviceLogging
from datetime import date,datetime
import logging

LOGGER = logging.getLogger(__name__)

def print_logs_to_file(s,d,log_name,status='ok'):
    if status=='ok':
        filename_d = 'logs_test_{}_{}.csv'.format(log_name,datetime.now().strftime('%d_%m_%Y-%H_%M'))
        filename_s = 'states_test_{}_{}.csv'.format(log_name,datetime.now().strftime('%d_%m_%Y-%H_%M'))
    elif status=='error':
        filename_d = 'error_logs_test_{}_{}.csv'.format(log_name,datetime.now().strftime('%d_%m_%Y-%H_%M'))
        filename_s = 'error_states_test_{}_{}.csv'.format(log_name,datetime.now().strftime('%d_%m_%Y-%H_%M'))
    LOGGER.info("Printing log files to build/{} and build/{}".format(filename_d,filename_s))
    d.implementation.print_log_to_file(filename_d,style='csv')
    s.print_records_to_file(filename_s,style='csv',filtered=False)

def log_it(log_name,devices_to_log,non_default_states_to_check):
    def decorator_log_it(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            s = StateChecker(devices_to_log,specific_states=non_default_states_to_check)
            s.run(threaded=True,resolution=0.1)
            d = DeviceLogging('DeviceLoggingImplWithDBDirect')
            d.update_traces(devices_to_log)
            d.start_tracing()  
            ################ 
            try:
                result = func(*args, **kwargs)
            except:
                s.stop()
                d.stop_tracing()
                LOGGER.info("error in executing SUT")
                print_logs_to_file(s,d,log_name,status='error')
                raise
            ################
            s.stop()
            d.stop_tracing()
            print_logs_to_file(s,d,log_name,status='ok')
            return result
        return wrapper
    return decorator_log_it

