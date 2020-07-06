from aiohttp import web
import pytest 
import asyncio 
import logging
from queue import Queue
from aiojobs.aiohttp import setup, spawn, get_scheduler_from_app, get_scheduler_from_request
from time import sleep
from ska.logging import configure_logging
# app modules
from exploration.web_pytest.test_executor import validate_it, validate_test_spec,run_test
from exploration.web_pytest.async_threading import async_is_empty_on_queue, get_async_from_queue,AsyncThreadRunner

routes = web.RouteTableDef()
configure_logging()
LOGGER = logging.getLogger(__name__)

# entry points

@routes.get('/dev-testing/ping')
async def ping(request):
    LOGGER.info(f"test request received {request}")
    return web.Response(text="pong")


@routes.post('/dev-testing/test')
@validate_it(validate_test_spec)
async def request_test(request):
    LOGGER.info(f"test request received {request}")
    test_spec = await request.json()
    await spawn(request, run_test(test_spec,request.app))
    return web.json_response(test_spec)


@routes.get('/dev-testing/results')
async def get_results(request):
    LOGGER.info(f"test request received {request}")
    queue = request.app['test_results']
    is_queue_empty = await async_is_empty_on_queue(queue)
    if is_queue_empty:
        return web.Response(text="Test not finished")
    else:
        results = await get_async_from_queue(queue)
        return web.Response(text=f"Test Results: {results}")



async def wait_until_tests_finished(app):
    jobs = get_scheduler_from_app(app)
    for job in jobs:
        await job.wait()


 # app creation


def create_app():
    app = web.Application()
    runner = AsyncThreadRunner()
    runner.__init__()
    setup(app)
    app.add_routes(routes)
    app['test_results'] = Queue()
    return app


if __name__ == "__main__":
    app = create_app()
    LOGGER.info(f"starting app")
    web.run_app(app, port=8010)