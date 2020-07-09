from aiohttp import web
import functools
import pytest
import asyncio
from exploration.web_pytest.async_threading import async_thread_it

test_spec_schema = {
        'path' : {'error_message':'test path not given'},
        'module': {'error_message':'test module not given'},
        'test': {'error_message':'test not given'},
}

# decorators
# #############
def validate_it(validate):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(request):
            result = await validate(request)
            if result['valid']:
                return await func(request)
            else:
                return result['response']
        return wrapper
    return decorator

# ###############
async def validate_test_spec(request):
    test_spec = await request.json()
    test_spec_keys = test_spec.keys()
    errors = []
    result = {}
    for key in test_spec_schema.keys():
        if key not in test_spec_keys:
            errors.append(test_spec_schema[key])
    if errors:
        result['valid'] = False
        error_message = "Error in validating test specification\n"
        error_message += functools.reduce(lambda x,y: x+'\n'+y,errors)
        result['response'] = web.HTTPBadRequest()
        return result
    else:
        result['valid'] = True
        return result


@async_thread_it
def run_test(test_spec,app):
    test_str =  f"/home/tango/skampi/post-deployment/"\
                f"{test_spec['path']}"\
                f"{test_spec['module']}"\
                f"::{test_spec['test']}"
    results = pytest.main([test_str]) 
    app['test_results'].put(results)
    


    