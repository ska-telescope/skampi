import functools
from resources.test_support.helpers import waiter,watch,resource
from contextlib import contextmanager
import signal
import logging
from contextlib import contextmanager
from tango import DeviceProxy

# pre cheks
def check_going_out_of_empty():
    ## Verify the Subarray obstate = EMPTY
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('EMPTY')

def check_going_into_configure():
    ## Can only configure a subarray that is in State ON and obsState IDLE/READY
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals(['IDLE','READY'])
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')


def check_going_into_abort():
    ## Can only invoke abort on a subarray when in IDLE, SCANNING, CONFIGURING, READY, RESETTING
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals(['IDLE','SCANNING','CONFIGURING','READY','RESETTING'])
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')

def check_going_into_restart():
    ## Can only invoke restart on a subarray when in ABORTED, FAULT
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals(['ABORTED','FAULT'])
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')

def check_coming_out_of_standby():
    ## Verify the Subarray State = OFF
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('OFF')

def check_going_out_of_configured():
    ## Verify the Subarray obstate = READY
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
    # resource('mid_csp/elt/subarray_01').assert_attribute('obsState').equals('READY')
    # resource('mid_sdp/elt/subarray_1').assert_attribute('obsState').equals('READY')
    
def check_going_out_of_abort():
    ## Verify the Subarray obstate = ABORTED
    # resource('mid_csp/elt/subarray_01').assert_attribute('obsState').equals('ABORTED')
    # resource('mid_sdp/elt/subarray_1').assert_attribute('obsState').equals('ABORTED')
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('ABORTED')
    logging.info("Abort completed on Subarray")    

def check_going_into_empty():
    ## Can only release resources if subarray is in State ON and obsState IDLE
    logging.info("Check if the SubarrayNode State is ON and obsState is IDLE")
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')

def check_going_into_standby():
    logging.info("Check if the SubarrayNode State is ON")
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')

# pre waitings

class WaitConfigure():

    def __init__(self):
        self.w  = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState")
        self.w1  = watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("obsState")
        self.w2 = watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("obsState")

    def wait(self):
        self.w.wait_until_value_changed_to('READY',timeout=200)
        self.w1.wait_until_value_changed_to('READY',timeout=200)
        self.w2.wait_until_value_changed_to('READY',timeout=200)

    def wait_oet(self):
        self.w.wait_until_value_changed_to('READY',timeout=200)

class WaitConfiguring():

    def __init__(self):
        self.w  = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState")

    def wait(self, timeout):
        self.w.wait_until_value_changed_to('CONFIGURING',timeout=200)
    
class WaitAbort():

    def __init__(self):
        self.the_watch  = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState")

    def wait(self,timeout):
        # self.the_watch.wait_until_value_changed_to('ABORTING',timeout)
        logging.info("ABORT command invoked. Waiting for obsState to change to ABORTED")
        self.the_watch.wait_until_value_changed_to('ABORTED',timeout=200)

class WaitRestart():

    def __init__(self):
        self.the_watch  = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState")

    def wait(self,timeout):
        # self.the_watch.wait_until_value_changed_to('RESTARTING',timeout)
        logging.info("Restart command invoked. Waiting for obsState to change to EMPTY")
        self.the_watch.wait_until_value_changed_to('EMPTY',timeout=200)

class WaitObsReset():

    def __init__(self):
        self.the_watch  = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState")

    def wait(self,timeout):
        logging.info("ObsReset command invoked. Waiting for obsState to change to IDLE")
        self.the_watch.wait_until_value_changed_to('IDLE',timeout=200)

class WaitResetting():
    
    def __init__(self):
        self.the_watch  = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState")
        self.the_watch1  = watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("obsState")
        resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('ABORTED')
    
    def wait(self,timeout):
        logging.info("ObsReset command invoked. Waiting for obsState to change to Resetting")
        self.the_watch.wait_until_value_changed_to('RESETTING',timeout=200)
        self.the_watch1.wait_until_value_changed_to('IDLE',timeout=200)


class WaitScanning():
    def __init__(self):
        self.the_watch = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on('obsState')

    def wait(self,timeout):
        logging.info("Scan command invoked. Waiting for obsState to change to SCANNING")
        self.the_watch.wait_until_value_changed_to('SCANNING',timeout)
        logging.info("Waiting for obsState to change to READY")
        self.the_watch.wait_until_value_changed_to('READY',timeout)


def sync_assign_resources(nr_of_receptors=4,timeout=60):
# defined as a decorator
    def decorator_sync_assign_resources(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            check_going_out_of_empty()
            the_waiter = waiter()
            the_waiter.set_wait_for_assign_resources(nr_of_receptors=nr_of_receptors)
            ################ 
            result = func(*args, **kwargs)
            ################ 
            the_waiter.wait(timeout=timeout)
            return result
        return wrapper
    return decorator_sync_assign_resources


# defined as a context manager
@contextmanager
def sync_assigned_resources(nr_of_receptors=4):
    check_going_out_of_empty()
    the_waiter = waiter()
    the_waiter.set_wait_for_assign_resources(nr_of_receptors=nr_of_receptors)
    yield
    the_waiter.wait(timeout=60)
    

##this is only in the case of using TMC device proxies, OET command is blocking for the entire duration
def sync_configure(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ##Can only configure a subarray that is in IDLE/ON
        # Branch changes
        # resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals(['IDLE','READY'])
        # resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
        # w  = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState")
        # ################
        # result = func(*args, **kwargs)
        # ################
        # #w.wait_until_value_changed_to('CONFIGURING')
        # w.wait_until_value_changed_to('READY',timeout=200)
        check_going_into_configure()
        w  = WaitConfigure()
        ################ 
        result = func(*args, **kwargs)
        ################ 
        w.wait()
        return result
    return wrapper

# defined as a context manager
@contextmanager
def sync_configuration():
    check_going_into_configure()
    w = WaitConfigure()
    yield
    w.wait()


def sync_configure_oet(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ##Can only configure a subarray that is in IDLE/ON
        check_going_into_configure()
        w = WaitConfigure()
        ################ 
        result = func(*args, **kwargs)
        ################ 
        w.wait()
        w.wait_oet()
        return result
    return wrapper


def sync_configuring(timeout=200):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            check_going_into_configure()
            w = WaitConfiguring()
            ################
            result = func(*args, **kwargs)
            ################
            w.wait(timeout)
            return result
        return wrapper
    return decorator

# defined as a context manager
@contextmanager
def sync_oet_configuration():
    check_going_into_configure()
    w = WaitConfigure()
    yield
    w.wait_oet()


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

# defined as a context manager
@contextmanager
def limited_time_routine(timeout):
    signal.signal(signal.SIGALRM, handle_timeout)
    signal.alarm(timeout)  # wait for timeout seconds and timeout if still stick
    yield
    signal.alarm(0)


def sync_start_up_telescope(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        check_coming_out_of_standby()
        the_waiter = waiter()
        the_waiter.set_wait_for_starting_up()
        result = func(*args, **kwargs)
        the_waiter.wait(50)
        return result
    return wrapper

# defined as a context manager
@contextmanager
def sync_telescope_starting_up(timeout=50):
    check_coming_out_of_standby()
    the_waiter = waiter()
    the_waiter.set_wait_for_starting_up()
    yield
    the_waiter.wait(timeout)

def sync_end_sb(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        check_going_out_of_configured()
        the_waiter = waiter()
        the_waiter.set_wait_for_ending_SB()
        result = func(*args, **kwargs)
        the_waiter.wait(200)
        return result
    return wrapper

def sync_restart_sa(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        check_going_out_of_abort()
        the_waiter = waiter()
        the_waiter.set_wait_for_going_into_restarting()
        result = func(*args, **kwargs)
        the_waiter.wait(100)
        return result
    return wrapper

def sync_reset_sa(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        check_going_out_of_abort()
        the_waiter = waiter()
        the_waiter.set_wait_for_going_into_obsreset()
        result = func(*args, **kwargs)
        the_waiter.wait(100)
        return result
    return wrapper

# defined as a context manager
@contextmanager
def sync_sb_ending():
    check_going_out_of_configured()
    the_waiter = waiter()
    the_waiter.set_wait_for_ending_SB()
    yield
    the_waiter.wait()

def sync_release_resources(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print("In sync_release_resources")
        check_going_into_empty()
        the_waiter = waiter()
        the_waiter.set_wait_for_tearing_down_subarray()
        result = func(*args, **kwargs)
        the_waiter.wait(150)
        return result
    return wrapper

# defined as a context manager
@contextmanager
def sync_resources_releasing(timeout=100):
    the_waiter = waiter()
    the_waiter.set_wait_for_tearing_down_subarray()
    yield
    the_waiter.wait(timeout)


def sync_set_to_standby(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        check_going_into_standby()
        the_waiter = waiter()
        the_waiter.set_wait_for_going_to_standby()
        result = func(*args, **kwargs)
        the_waiter.wait(100)
        return result
    return wrapper

# defined as a context manager
@contextmanager
def sync_going_to_standby(timeout=50):
    check_going_into_standby()
    the_waiter = waiter()
    the_waiter.set_wait_for_going_to_standby()
    yield
    the_waiter.wait(timeout)

def sync_scan(timeout=200):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            check_going_out_of_configured()
            w = WaitScanning()
            result = func(*args, **kwargs)
            w.wait(timeout)
            return result
        return wrapper
    return decorator

def sync_abort(timeout=200):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            check_going_into_abort()
            w = WaitAbort()
            ################
            result = func(*args, **kwargs)
            ################
            w.wait(timeout)
            return result
        return wrapper
    return decorator

def sync_restart(timeout=200):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            #check_going_into_restart()
            check_going_out_of_abort()
            w = WaitRestart()
            ################
            result = func(*args, **kwargs)
            ################
            w.wait(timeout)
            return result
        return wrapper
    return decorator

def sync_obsreset(timeout=200):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            #check_going_into_resetting()
            check_going_out_of_abort()
            w = WaitObsReset()
            ################
            result = func(*args, **kwargs)
            ################
            w.wait(timeout)
            return result
        return wrapper
    return decorator

def sync_resetting(timeout=200):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            check_going_out_of_abort()
            w = WaitResetting()
            ################
            result = func(*args, **kwargs)
            ################
            w.wait(timeout)
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
        check_going_out_of_configured()
        the_waiter = waiter()
        the_waiter.set_wait_for_going_into_scanning()
        result = func(*args, **kwargs)
        the_waiter.wait()
        return result
    return wrapper
    

# defined as a context manager
@contextmanager
def sync_oet_scanning(timeout=200):
    check_going_out_of_configured()
    the_waiter = waiter()
    the_waiter.set_wait_for_going_into_scanning()
    yield
    the_waiter.wait()