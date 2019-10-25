# -*- coding: utf-8 -*-
"""
Some simple unit tests of the PowerSupply device, exercising the device from
the same host as the tests by using a DeviceTestContext.
"""
import requests
import json
import sys
from time import sleep

def test_init():    
  print("Init start-up-telescope")

def test_start_up_telescope():
  jsonLogin={"username":"user1","password":"abc123"}
  url = 'http://webjive-webjive-test:8080/login' 
  r = requests.post(url=url, json=jsonLogin)
  webjive_jwt = r.cookies.get_dict()['webjive_jwt']
    
  cookies = {'webjive_jwt': webjive_jwt}

  url = 'http://webjive-webjive-test:5004/db' 
  with open('files/mutation.json', 'r') as file:
    mutation = file.read().replace('\n', '')

  jsonMutation = json.loads(mutation)
  r = requests.post(url=url, json=jsonMutation, cookies=cookies)
  #print(r.text)
  parsed = json.loads(r.text)
  print(json.dumps(parsed, indent=4, sort_keys=True))
  assert parsed['data']['executeCommand']['ok'] == True