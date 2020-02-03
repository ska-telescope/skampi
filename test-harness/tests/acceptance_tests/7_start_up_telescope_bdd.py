# -*- coding: utf-8 -*-
""" A reimplementation of test 2, the telescope startup test, using Behaviour Driven Design (BDD).
"""

from pytest_bdd import scenario, given, when, then
import requests
import json
import sys
import logging
import pytest

@pytest.mark.xfail
@scenario("./1.feature", "Telescope startup")
def telescope_start():
    logging.info("Testing Telescope Startup")

@given("a telescope configuration file and a running webjive instance")
def config_location(run_context):
  jsonLogin={"username":"user1","password":"abc123"}
  url = 'http://webjive-webjive-{}:8080/login'.format(run_context.HELM_RELEASE)
  r = requests.post(url=url, json=jsonLogin)
  webjive_jwt = r.cookies.get_dict()['webjive_jwt']

  cookies = {'webjive_jwt': webjive_jwt}

  url = 'http://webjive-webjive-{}:5004/db'.format(run_context.HELM_RELEASE)
  # with open('test-harness/files/mutation.json', 'r') as file:
  #   mutation = file.read().replace('\n', '')
  mutation = '{"query":"mutation {\\n  executeCommand(device: \\"ska_mid/tm_central/central_node\\", command: \\"StartUpTelescope\\") {\\n    ok\\n    output\\n    message\\n  }\\n}\\n","variables":"null"}'
  jsonMutation = json.loads(mutation)
  r = requests.post(url=url, json=jsonMutation, cookies=cookies)
  return r

@when("the configuration file is passed to webjive")
@pytest.fixture
def parse_config(config_location):
  """ Webjive has already processed the config - this isn't strictly true, and I need to rewrite the .feature file.
  """
  parsed = json.loads(config_location.text)
  logging.info(json.dumps(parsed, indent=4, sort_keys=True))
  return parsed

@then("the telescope is configured")
def test_config(parse_config):
  assert parse_config['data']['executeCommand']['ok'] == True
