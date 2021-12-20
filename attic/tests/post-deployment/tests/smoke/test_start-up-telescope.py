# -*- coding: utf-8 -*-
"""
Some simple unit tests of the PowerSupply device, exercising the device from
the same host as the tests by using a DeviceTestContext.
"""
import requests
import json
import sys
from time import sleep
import pytest
from resources.test_support.helpers import waiter
from resources.test_support.controls import set_telescope_to_standby, telescope_is_in_standby, tmc_is_on
import logging

LOGGER = logging.getLogger(__name__)


@pytest.mark.fast
def test_init():    
  print("Init start-up-telescope")

@pytest.mark.skip
@pytest.mark.fast
@pytest.mark.skamid
def test_start_up_telescope(run_context):
  LOGGER.info("Before starting the telescope checking if the TMC is in ON state")
  assert(tmc_is_on())
  LOGGER.info("Before starting the telescope checking if the telescope is in StandBy.")
  assert(telescope_is_in_standby)
  jsonLogin={"username":"user1","password":"abc123"}
  url = 'http://taranta-taranta-{}:8080/login'.format(run_context.HELM_RELEASE)
  r = requests.post(url=url, json=jsonLogin)
  taranta_jwt = r.cookies.get_dict()['taranta_jwt']
    
  cookies = {'taranta_jwt': taranta_jwt}

  url = 'http://taranta-taranta-{}:5004/db'.format(run_context.HELM_RELEASE)
  # with open('test-harness/files/mutation.json', 'r') as file:
  #   mutation = file.read().replace('\n', '')
  mutation = '{"query":"mutation {\\n  executeCommand(device: \\"ska_mid/tm_central/central_node\\", command: \\"TelescopeOn\\") {\\n    ok\\n    output\\n    message\\n  }\\n}\\n","variables":"null"}'
  LOGGER.info("Mutation " + str(mutation))
  jsonMutation = json.loads(mutation)
  LOGGER.info("jsonMutation "+ str(jsonMutation))
  the_waiter = waiter()
  the_waiter.set_wait_for_starting_up()
  r = requests.post(url=url, json=jsonMutation, cookies=cookies)
  the_waiter.wait()
  LOGGER.info("r.text " + str(r.text))
  parsed = json.loads(r.text)
  LOGGER.info("parsed r.text is " + str(parsed))
  print(json.dumps(parsed, indent=4, sort_keys=True))
  LOGGER.info("sorted pasrsed r.text " + str(json.dumps(parsed, indent=4, sort_keys=True)))
  try:
    assert parsed['data']['executeCommand']['ok'] == True
  finally:
    # tear down command is ignored if it is already in standby
    if not telescope_is_in_standby():
      # wait first for telescope to completely go to standby before switchig it off again    
      set_telescope_to_standby()
    LOGGER.info("Telescope is in STANDBY")