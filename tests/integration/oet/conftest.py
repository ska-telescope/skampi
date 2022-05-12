"""Pytest fixtures and bdd step implementations specific to OET integration tests."""
import logging
from time import sleep
from pytest_bdd import given, when, then

import requests
LOGGER = logging.getLogger(__name__)


@given("the hello_world script is created in the OET")
def hello_world_script_created():
    request_json = {
        "script_args": {
            "init": dict(args=[], kwargs={"subarray_id": 1}),
        },
        "script": dict(script_type="filesystem", script_uri="file:///scripts/hello_world.py")
    }

    response = requests.post("http://ska-oso-oet-rest-test:5000/api/v1.0/procedures", json=request_json)

@when("the script is ran")
def hello_world_script_ran():

    procedures = requests.get("http://ska-oso-oet-rest-test:5000/api/v1.0/procedures")

    url = procedures.json()["procedures"][-1]["uri"]

    request_json = {"script_args": {"run": dict(args=[], kwargs={})}, "state": "RUNNING"}

    response = requests.put(url, json=request_json)


@then("script execution completes successfully")
def hello_world_script_complete():
    sleep(10)

    procedures = requests.get("http://ska-oso-oet-rest-test:5000/api/v1.0/procedures")

    url = procedures.json()["procedures"][-1]["uri"]

    response = requests.get(url)

    state = response.json()['procedure']['state']

    assert state == 'COMPLETED'

