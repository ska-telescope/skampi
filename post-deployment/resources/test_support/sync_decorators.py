import functools
from resources.test_support.helpers import waiter,watch,resource
import signal

def sync_assign_resources(nr_of_receptors=4):
    def decorator_sync_assign_resources(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            the_waiter = waiter()
            the_waiter.set_wait_for_assign_resources(nr_of_receptors=nr_of_receptors)
            ################ 
            result = func(*args, **kwargs)
            ################ 
            the_waiter.wait(timeout=40)
            return result
        return wrapper
    return decorator_sync_assign_resources


def sync_configure(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        w  = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState")
        ################ 
        result = func(*args, **kwargs)
        ################ 
        w.wait_until_value_changed_to('CONFIGURING')
        w.wait_until_value_changed_to('READY',timeout=200)
        return result
    return wrapper

def handlde_timeout(arg1,agr2):
    print("operation timeout")
    raise Exception("operation timeout")

def time_it(timeout):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, handlde_timeout)
            signal.alarm(timeout)  # wait for timeout seconds and timeout if still stick
            ################ 
            result = func(*args, **kwargs)
            ################ 
            return result
        return wrapper
    return decorator

def sync_start_up_telescope(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        the_waiter = waiter()
        the_waiter.set_wait_for_starting_up()
        func(*args, **kwargs)
        the_waiter.wait()
    return wrapper

def sync_end_sb(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        the_waiter = waiter()
        the_waiter.set_wait_for_ending_SB()
        func(*args, **kwargs)
        the_waiter.wait()
    return wrapper

def sync_release_resources(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        the_waiter = waiter()
        the_waiter.set_wait_for_tearing_down_subarray()
        func(*args, **kwargs)
        the_waiter.wait()
    return wrapper

def sync_set_to_standby(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        the_waiter = waiter()
        the_waiter.set_wait_for_going_to_standby()
        func(*args, **kwargs)
        the_waiter.wait()
    return wrapper

def sync_scan(timeout=200):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            the_watch = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on('obsState')
            func(*args, **kwargs)
            the_watch.wait_until_value_changed_to('SCANNING')
            the_watch.wait_until_value_changed_to('READY',timeout)
        return wrapper
    return decorator



