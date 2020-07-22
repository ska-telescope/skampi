import functools
from resources.test_support.state_checking import StateChecker
from resources.test_support.log_helping import DeviceLogging
from datetime import date,datetime
import logging
import os
from contextlib import contextmanager

VAR = os.environ.get('USE_LOCAL_ELASTIC')
if (VAR == "True"):
    local_elastic_disabled = False
else:
    local_elastic_disabled = True

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
        if local_elastic_disabled:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                s = StateChecker(devices_to_log,specific_states=non_default_states_to_check)
                s.run(threaded=True,resolution=0.1)
                d = DeviceLogging()
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


def print_states_logs_to_file(s,log_name,status='ok'):
    if status=='ok':
        filename_s = 'states_test_{}_{}.csv'.format(log_name,datetime.now().strftime('%d_%m_%Y-%H_%M'))
    elif status=='error':
        filename_s = 'error_states_test_{}_{}.csv'.format(log_name,datetime.now().strftime('%d_%m_%Y-%H_%M'))
    else:
        raise Exception(f'Incorrect status flag: status must be "ok" or "error" but {status} was given')
    LOGGER.info(f"Printing log state files to build/{filename_s}")
    s.print_records_to_file(filename_s,style='csv',filtered=False)

def print_log_messages_to_file(d,log_name,status='ok'):
    if status=='ok':
        filename_d = 'logs_test_{}_{}.csv'.format(log_name,datetime.now().strftime('%d_%m_%Y-%H_%M'))
    elif status=='error':
        filename_d = 'error_logs_test_{}_{}.csv'.format(log_name,datetime.now().strftime('%d_%m_%Y-%H_%M'))
    else:
        raise Exception(f'Incorrect status flag: status must be "ok" or "error" but {status} was given')
    LOGGER.info(f"Printing log messages files to build/{filename_d}")
    d.implementation.print_log_to_file(filename_d,style='csv')


@contextmanager
def log_messages(log_name,devices_to_log):
    d = DeviceLogging()
    d.update_traces(devices_to_log)
    d.start_tracing()
    try:
        yield
    except Exception as e:
        d.stop_tracing()
        #print_log_messages_to_file(d,log_name,status='error')
        raise e
    d.stop_tracing()
    #print_log_messages_to_file(d,log_name,status='ok')


@contextmanager
def log_states(log_name,devices_to_log,state_name='obsState',non_default_states_to_check={}):
    s = StateChecker(devices_to_log,state_name=state_name,specific_states=non_default_states_to_check)
    s.run(threaded=True,resolution=0.05)
    try:
        yield
    except Exception as e:
        s.stop()
        LOGGER.info("error in executing SUT")
        print_states_logs_to_file(s,log_name,status='error')
        raise e
    s.stop()
    print_states_logs_to_file(s,log_name,status='ok')



