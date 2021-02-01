# -*- coding: utf-8 -*-
"""
Test archiver
"""
import sys
import os
import pytest
import logging
from time import sleep
from resources.test_support.archiver import ArchiverHelper
from tango import DevFailed, DeviceProxy, GreenMode, AttributeProxy, ApiUtil, DeviceData

archiver_namespace = os.getenv('ARCHIVER_NAMESPACE')
mvp_tangodbserver = os.getenv('TANGO_DATABASE_DS')
conf_manager = \
  f'tango://databaseds-tango-base-test.{archiver_namespace}.svc.cluster.local:10000/archiving/hdbpp/confmanager01'
event_subscriber = \
  f'tango://databaseds-tango-base-test.{archiver_namespace}.svc.cluster.local:10000/archiving/hdbpp/eventsubscriber01'
attribute = f"tango://{mvp_tangodbserver}.svc.cluster.local:10000/ska_mid/tm_subarray_node/1/State"

@pytest.mark.archiver
@pytest.mark.skamid
# @pytest.mark.xfail
def test_init():
  print("Init test archiver")
  global conf_manager
  global event_subscriber
  archiver_helper = ArchiverHelper(conf_manager=conf_manager, eventsubscriber=event_subscriber)
  archiver_helper.start_archiving()

def configure_attribute(attribute):
  archiver_helper = ArchiverHelper()
  archiver_helper.attribute_add(attribute,100,300)
  archiver_helper.start_archiving()
  slept_for = archiver_helper.wait_for_start(attribute)
  logging.info("Slept for " + str(slept_for) + 's before archiving started.')
  assert "Archiving          : Started" in archiver_helper.conf_manager_attribute_status(attribute)
  assert "Archiving          : Started" in archiver_helper.evt_subscriber_attribute_status(attribute)
  archiver_helper.stop_archiving(attribute)

@pytest.mark.archiver
@pytest.mark.xfail
def test_configure_attribute():
  global attribute
  sleep_time = 20
  max_retries = 3
  total_slept = 0
  for x in range(0, max_retries):
    try:
      ApiUtil.cleanup()
      configure_attribute(attribute)
      break
    except DevFailed as df:
      logging.info("configure_attribute exception: " + str(sys.exc_info()))
      try:
        deviceAdm = DeviceProxy("dserver/hdbppcm-srv/01")
        deviceAdm.RestartServer()
      except:
        logging.info("reset_conf_manager exception: " + str(sys.exc_info()[0]))
      if(x == (max_retries - 1)):
        raise df

    sleep(sleep_time)
    total_slept += 1

  if(total_slept>0):
    logging.info("Slept for " + str(total_slept*sleep_time) + 's for the test configuration!')

@pytest.mark.archiver
@pytest.mark.xfail
def test_archiving_started():
  archiver_helper = ArchiverHelper()
  assert archiver_helper.is_started(f"tango://{mvp_tangodbserver}.svc.cluster.local:10000/ska_mid/tm_subarray_node/1/State")
