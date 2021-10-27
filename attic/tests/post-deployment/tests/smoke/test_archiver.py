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
from tango import DevFailed, DeviceProxy, GreenMode, AttributeProxy, ApiUtil, DeviceData # type: ignore

@pytest.mark.archiver
@pytest.mark.skamid
#@pytest.mark.skip(reason="Archiver deployment is disabled from pipeline")
def test_mid_archiver():
  logging.info("Init test archiver")
  mvp_tango_host = os.getenv('TANGO_HOST')[:-6]
  mvp_namespace = os.getenv('KUBE_NAMESPACE')

  conf_manager = \
    f'tango://{mvp_tango_host}:10000/archiving/hdbpp/confmanager01'
  event_subscriber = \
    f'tango://{mvp_tango_host}:10000/archiving/hdbpp/eventsubscriber01'
  attribute = f"tango://{mvp_tango_host}:10000/ska_mid/tm_leaf_node/sdp_subarray01/healthState"
  
  logging.info(f'MVP namespace       : {mvp_namespace}')
  logging.info(f'MVP Tango host      : {mvp_tango_host}')
  logging.info(f'Config manager      : {conf_manager}')
  logging.info(f'Event subscriber    : {event_subscriber}')

  # Configure
  archiver_helper = ArchiverHelper(conf_manager=conf_manager, eventsubscriber=event_subscriber)
  archiver_helper.start_archiving(attribute)

  slept_for = archiver_helper.wait_for_start(attribute)
  logging.info("Slept for " + str(slept_for) + 's before archiving started.')

  # Assert
  assert "Archiving          : Started" in archiver_helper.conf_manager_attribute_status(attribute)
  assert "Archiving          : Started" in archiver_helper.evt_subscriber_attribute_status(attribute)

  # Teardown
  archiver_helper.stop_archiving(attribute)

@pytest.mark.archiver
@pytest.mark.skalow
#@pytest.mark.skip(reason="Archiver deployment is disabled from pipeline")
def test_low_archiver():
  logging.info("Init test archiver")
  mvp_tango_host = os.getenv('TANGO_HOST')[:-6]
  mvp_namespace = os.getenv('KUBE_NAMESPACE')

  conf_manager = \
    f'tango://{mvp_tango_host}:10000/archiving/hdbpp/confmanager01'
  event_subscriber = \
    f'tango://{mvp_tango_host}:10000/archiving/hdbpp/eventsubscriber01'
  attribute = f"tango://{mvp_tango_host}:10000/ska_low/tm_leaf_node/mccs_subarray01/healthState"

  logging.info(f'MVP namespace       : {mvp_namespace}')
  logging.info(f'MVP Tango host      : {mvp_tango_host}')
  logging.info(f'Config manager      : {conf_manager}')
  logging.info(f'Event subscriber    : {event_subscriber}')

  # Configure
  archiver_helper = ArchiverHelper(conf_manager=conf_manager, eventsubscriber=event_subscriber)
  archiver_helper.start_archiving(attribute)

  slept_for = archiver_helper.wait_for_start(attribute)
  logging.info("Slept for " + str(slept_for) + 's before archiving started.')

  # Assert
  assert "Archiving          : Started" in archiver_helper.conf_manager_attribute_status(attribute)
  assert "Archiving          : Started" in archiver_helper.evt_subscriber_attribute_status(attribute)

  # Teardown
  archiver_helper.stop_archiving(attribute)
