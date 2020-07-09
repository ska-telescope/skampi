import functools
from resources.test_support.helpers import waiter,watch,resource
import signal
import logging
from contextlib import contextmanager

def check_going_out_of_configured():
    ##Can only return to ON/IDLE if in READY
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')

class WaitScanning():
    
    def __init__(self):
        self.the_watch = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on('obsState')

    def wait(self,timeout):
        self.the_watch.wait_until_value_changed_to('SCANNING')
        self.the_watch.wait_until_value_changed_to('READY',timeout)


def sync_assign_resources(nr_of_receptors=4,timeout=60):
    def decorator_sync_assign_resources(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
            the_waiter = waiter()
            the_waiter.set_wait_for_assign_resources(nr_of_receptors=nr_of_receptors)
            ################ 
            result = func(*args, **kwargs)
            ################ 
            the_waiter.wait(timeout=timeout)
            return result
        return wrapper
    return decorator_sync_assign_resources

##this is only in the case of using TMC device proxies, OET command is blocking for the entire duration
def sync_configure(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ##Can ony configure a subarray that is in IDLE/ON
        resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals(['IDLE','READY'])
        resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
        w  = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState")
        ################ 
        result = func(*args, **kwargs)
        ################ 
        #w.wait_until_value_changed_to('CONFIGURING')
        w.wait_until_value_changed_to('READY',timeout=200)
        return result
    return wrapper

def sync_configure_oet(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ##Can ony configure a subarray that is in IDLE/ON
        resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals(['IDLE','READY'])
        resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
        w  = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState")
        ################ 
        result = func(*args, **kwargs)
        ################ 
        w.wait_until_value_changed_to('READY',timeout=20)
        return result
    return wrapper

def handle_timeout(arg1,agr2):
    print("operation timeout")
    raise Exception("operation timeout")

def time_it(timeout):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, handle_timeout)
            signal.alarm(timeout)  # wait for timeout seconds and timeout if still stick
            ################ 
            result = func(*args, **kwargs)
            ################ 
            signal.alarm(0)
            return result
        return wrapper
    return decorator

def sync_start_up_telescope(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ##Can  only start up a disabled telescope
        resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('DISABLE')
        the_waiter = waiter()
        the_waiter.set_wait_for_starting_up()
        result = func(*args, **kwargs)
        the_waiter.wait(50)
        return result
    return wrapper

def sync_end_sb(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ##Can only return to ON/IDLE if in READY
        resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
        the_waiter = waiter()
        the_waiter.set_wait_for_ending_SB()
        result = func(*args, **kwargs)
        the_waiter.wait()
        return result
    return wrapper

def sync_release_resources(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ##Can only release resources if subarray is in ON/IDLE
        resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
        resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
        the_waiter = waiter()
        the_waiter.set_wait_for_tearing_down_subarray()
        result = func(*args, **kwargs)
        the_waiter.wait(50)
        return result
    return wrapper

def sync_set_to_standby(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('OFF')
        the_waiter = waiter()
        the_waiter.set_wait_for_going_to_standby()
        result = func(*args, **kwargs)
        the_waiter.wait(50)
        return result
    return wrapper

def sync_scan(timeout=200):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
            the_watch = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on('obsState')
            result = func(*args, **kwargs)
            logging.info("scan command dispatched, checking that the state transitioned to SCANNING")
            the_watch.wait_until_value_changed_to('SCANNING',timeout)
            logging.info("state transitioned to SCANNING, waiting for it to return to READY")
            the_watch.wait_until_value_changed_to('READY',timeout)
            return result
        return wrapper
    return decorator

# defined as a context manager
@contextmanager
def sync_scanning(timeout=200):
    check_going_out_of_configured()
    w = WaitScanning()
    yield
    w.wait(timeout)


def sync_scan_oet(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
        the_waiter = waiter()
        the_waiter.set_wait_for_going_into_scanning()
        result = func(*args, **kwargs)
        the_waiter.wait()
        return result
    return wrapper




