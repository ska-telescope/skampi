# -*- coding: utf-8 -*-
"""
Test archiver
"""
import logging
import sys
from time import sleep

import pytest
from tango import DevFailed, DeviceProxy, ApiUtil

from archiver_helper import ArchiverHelper

CONF_MANAGER_LOW = "low-eda/cm/01"
EVENT_SUBSCRIBER_LOW = "low-eda/es/01"
CONF_MANAGER = "mid-eda/cm/01"
EVENT_SUBSCRIBER = "mid-eda/es/01"
CM_SERVER = "dserver/hdbppcm-srv/01"


@pytest.mark.post_deployment
@pytest.mark.skalow
def test_init_low():
    logging.info("Init test archiver low device")
    archiver_helper = ArchiverHelper(CONF_MANAGER_LOW, EVENT_SUBSCRIBER_LOW)
    archiver_helper.start_archiving()


@pytest.mark.post_deployment
@pytest.mark.skamid
def test_init():
    logging.info("Init test archiver mid")
    archiver_helper = ArchiverHelper(CONF_MANAGER, EVENT_SUBSCRIBER)
    archiver_helper.start_archiving()


def configure_attribute(attribute, configuration_manager, event_subsrciber, strategy):
    archiver_helper = ArchiverHelper(configuration_manager, event_subsrciber)
    archiver_helper.attribute_add(attribute, 100, 300, strategy)
    archiver_helper.start_archiving()
    slept_for = archiver_helper.wait_for_start(attribute)
    logging.info("Slept for " + str(slept_for) + 's before archiving started.')
    assert "Archiving          : Started" in archiver_helper.conf_manager_attribute_status(attribute)
    assert "Archiving          : Started" in archiver_helper.evt_subscriber_attribute_status(attribute)
    archiver_helper.stop_archiving(attribute)


def test_configure_attribute(configuration_manager, event_subscriber, attribute, strategy):
    attribute = attribute
    sleep_time = 20
    max_retries = 3
    total_slept = 0
    for x in range(0, max_retries):
        try:
            ApiUtil.cleanup()
            configure_attribute(attribute, configuration_manager, event_subscriber, strategy)
            break
        except DevFailed as df:
            logging.info("configure_attribute exception: " + str(sys.exc_info()))
            try:
                deviceAdm = DeviceProxy(CM_SERVER)
                deviceAdm.RestartServer()
            except:
                logging.info("reset_conf_manager exception: " + str(sys.exc_info()[0]))
            if (x == (max_retries - 1)):
                raise df

        sleep(sleep_time)
        total_slept += 1

    if (total_slept > 0):
        logging.info("Slept for " + str(total_slept * sleep_time) + 's for the test configuration!')


@pytest.mark.post_deployment
@pytest.mark.skamid
@pytest.mark.parametrize(
    "attribute, strategy", [("sys/tg_test/1/double_scalar", "SetPeriodEvent"),
                            ("ska_mid/tm_central/central_node/state", "SetCodePushedEvent"),
                            ("ska_mid/tm_central/central_node/healthstate", "SetRelativeEvent"),
                            ("ska_mid/tm_central/central_node/telescopestate", "SetAbsoluteEvent")
                            ])
def test_config_attribute_mid(attribute, strategy):
    try:
        test_configure_attribute(CONF_MANAGER, EVENT_SUBSCRIBER, attribute, strategy)
    except Exception as e:
        logging.error(e)


@pytest.mark.post_deployment
@pytest.mark.skalow
@pytest.mark.parametrize(
    "attribute, strategy", [("sys/tg_test/1/double_scalar", "SetPeriodEvent"),
                            ("ska_low/tm_central/central_node/state", "SetCodePushedEvent"),
                            ("ska_low/tm_central/central_node/healthstate", "SetRelativeEvent"),
                            ("ska_low/tm_central/central_node/telescopestate", "SetAbsoluteEvent")
                            ])
def test_config_attribute_low(attribute, strategy):
    try:
        test_configure_attribute(CONF_MANAGER_LOW, EVENT_SUBSCRIBER_LOW, attribute, strategy)
    except Exception as e:
        logging.error(e)
