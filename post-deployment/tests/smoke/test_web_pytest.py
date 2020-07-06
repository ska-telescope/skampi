import pytest
import asyncio
import logging
import threading
import queue
from time import sleep
from assertpy import assert_that
from aiohttp.test_utils import TestClient, TestServer
import  mock
# the SUT
from exploration.web_pytest import web_pytest
from exploration.web_pytest import async_threading




@pytest.mark.asyncio
@pytest.fixture
async def test_client(event_loop):
    # given a running web app (SUT)
    logging.info("Setting up server")
    app = web_pytest.create_app()
    async with TestClient(TestServer(app), loop=event_loop) as client:
        yield client
        logging.info("tearing down server")
        await web_pytest.wait_until_tests_finished(app)

@pytest.mark.asyncio
async def test_can_ping_web(test_client):
    # given a test client connected to SUT
    # when I send the get command with ping
    resp = await test_client.get('/dev-testing/ping')
    # I expect a 200 return with text = "pong"
    assert_that(resp.status).is_equal_to(200)
    text = await resp.text()
    assert_that(text).is_equal_to('pong')


def mock_test(test_str):
    logging.info(f'spawned mock test started')
    sleep(0.5)
    logging.info('spawned test finished')
    return ('test finished')



@pytest.mark.asyncio
@mock.patch('exploration.web_pytest.test_executor.pytest.main')
async def test_submit_test(mock_test_run,test_client):
    # given a test client connected to SUT
    # when I submit a new test according to test spec
    mock_test_run.side_effect = mock_test
    test_spec = {
        'path' : 'tests/smoke',
        'module': 'test_waiting.py',
        'test': 'test_can_ping_web',
    }
    resp = await test_client.post('/dev-testing/test',json = test_spec)
    # I expect a 200 return with returned json equals requested test_spec
    assert_that(resp.status).is_equal_to(200)
    returned_test_spec = await resp.json()
    assert_that(returned_test_spec).is_equal_to(test_spec)
    # then after querying immediately afterwards for results
    resp = await test_client.get('/dev-testing/results')
    # I expect a Test not finished" response
    text = await resp.text()
    assert_that(text).is_equal_to("Test not finished")
    

@pytest.mark.asyncio
@mock.patch('exploration.web_pytest.test_executor.pytest.main')
async def test_submit_test_and_wait(mock_test_run,test_client):
    # given a test client connected to SUT
    # when I submit a new test according to test spec
    mock_test_run.side_effect = mock_test
    test_spec = {
        'path' : 'tests/smoke',
        'module': 'test_waiting.py',
        'test': 'test_can_ping_web',
    }
    resp = await test_client.post('/dev-testing/test',json = test_spec)
    # I expect a 200 return with returned json equals requested test_spec
    assert_that(resp.status).is_equal_to(200)
    returned_test_spec = await resp.json()
    assert_that(returned_test_spec).is_equal_to(test_spec)
    # then given the test has completed
    await web_pytest.wait_until_tests_finished(test_client.app)
    # when I query the results
    resp = await test_client.get('/dev-testing/results')
    # I expect a Test not finished" response
    text = await resp.text()
    assert_that(text).is_equal_to("Test Results: test finished")


@pytest.mark.asyncio
async def test_get_empty_response_on_results_request(test_client):
    # given a test client connected to SUT
    resp = await test_client.get('/dev-testing/results')
    # I expect a Test not finished" response
    text = await resp.text()
    assert_that(text).is_equal_to("Test not finished")

class ThreadedProducer():

    def __init__(self,load,queue,nr_of_ticks_before_pausing=2):
        self.load = load
        self.task = None
        self.q = queue
        self.signal_to_continue = threading.Event()
        self.nr_of_ticks_before_pausing = nr_of_ticks_before_pausing
 
    def _produce(self):
        ticks = 0
        for i in range(self.load):
            self.q.put(i)
            ticks += 1
            if ticks == self.nr_of_ticks_before_pausing:
                self.signal_to_continue.wait()
                self.signal_to_continue.clear()
                ticks = 0
   
    def continue_producing(self):
        self.signal_to_continue.set()

    def is_paused(self):
        return not self.signal_to_continue.is_set()

    def start_producing(self):
        self.task = threading.Thread(target=self._produce)
        self.signal_to_continue.clear()
        self.task.start()


@pytest.mark.asyncio
async def test_can_put_on_blocking_queue():
    #  give a producer creating 10 work items
    q = queue.LifoQueue()
    runner = async_threading.AsyncThreadRunner()
    runner.__init__()
    load = 10
    p = ThreadedProducer(load,q)
    # when the producer starts producing them
    p.start_producing()
    # I can collect them by means of ann async thread command
    # in order for this to happen concurrently the current item
    # on the queue must be collexted before all of the items are 
    # if they are in lock step 2 (e.g. it pauses until queu is emmpty) it means output must be
    # [1, 0, 3, 2, 5, 4, 7, 6, 9, 8]
    items = []
    for i in range(load):
        item = await async_threading.get_async_from_queue(q)
        items.append(item)
        if await async_threading.async_is_empty_on_queue(q):
           p.continue_producing() 
    logging.info(items)
    assert_that(items).is_equal_to([1, 0, 3, 2, 5, 4, 7, 6, 9, 8])



   
    
    



