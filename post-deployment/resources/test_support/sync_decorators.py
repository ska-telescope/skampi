import functools
from resources.test_support.helpers import waiter,watch,resource

def sync_assign_resources(nr_of_receptors=4):
    def decorator_sync_assign_resources(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            the_waiter = waiter()
            the_waiter.set_wait_for_assign_resources(nr_of_receptors=nr_of_receptors)
            ################ 
            result = func(*args, **kwargs)
            ################ 
            the_waiter.wait()
            return result
        return wrapper
    return decorator_sync_assign_resources


def sync_configure(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        w  = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState",changed_to='READY')
        ################ 
        result = func(*args, **kwargs)
        ################ 
        the_waiter.wait()
        return result
    return wrapper
    