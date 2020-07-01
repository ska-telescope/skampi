import functools
import asyncio
from concurrent.futures import ThreadPoolExecutor

def singleton(cls):
    """
    A factory that wraps the call to create a new instance of a 
    class by returning the same instance of it already exists
    """
    @functools.wraps(cls)
    def factory_wrapper(*args, **kwargs):
        if factory_wrapper.instance is None:
            factory_wrapper.instance = cls(*args, **kwargs)
        return factory_wrapper.instance
    factory_wrapper.instance = None
    return factory_wrapper

@singleton
class AsyncThreadRunner():

    def __init__(self, max_workers=5):
        self.loop = asyncio.get_running_loop()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def run_thread_and_await_result(self,func,*args,**kwargs):
        return await self.loop.run_in_executor(self.executor,
                                        func,*args,**kwargs)
    
    def shutdown(self):
        self.executor.shutdown()


def async_thread_it(func):
    @functools.wraps(func)
    async def wrapper(*args,**kwargs):
        runner = AsyncThreadRunner()
        return await runner.run_thread_and_await_result(func,*args,**kwargs)
    return wrapper
'''
    wraps around a thread safe queue by ensuring
    any blocking operations (e.g. by waiting for
    threadinglock) is turned into an await on the event loop
'''
@async_thread_it
def get_async_from_queue(queue):
    return queue.get()

@async_thread_it
def put_async_on_queue(queue,item):
    queue.put(item)

@async_thread_it
def async_is_empty_on_queue(queue):
    return queue.empty()

@async_thread_it
def async_join_queue(queue):
    queue.join()

@async_thread_it
def async_task_done_on_queue(queue):
    queue.task_done()