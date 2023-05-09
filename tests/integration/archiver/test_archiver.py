# -*- coding: utf-8 -*-
"""
Test archiver
"""
import logging
import sys,os
from time import sleep

import pytest
from tango import DevFailed, DeviceProxy, ApiUtil

from .archiver_helper import ArchiverHelper

CONFIG = os.getenv("CONFIG")
CONF_MANAGER = f"{CONFIG}-eda/cm/01"
EVENT_SUBSCRIBER = f"{CONFIG}-eda/es/01"
CM_SERVER = "dserver/hdbppcm-srv/01"



@pytest.mark.post_deployment
@pytest.mark.skamid
@pytest.mark.skalow
def test_init():
    logging.info("Init test archiver mid")
    archiver_helper = ArchiverHelper(CONF_MANAGER, EVENT_SUBSCRIBER)
    archiver_helper.start_archiving()


def configure_attribute(attribute, configuration_manager, event_subscriber, strategy, value):
    archiver_helper = ArchiverHelper(configuration_manager, event_subscriber)
    archiver_helper.attribute_add(attribute, strategy,1000, value)
    archiver_helper.start_archiving()
    slept_for = archiver_helper.wait_for_start(attribute)
    logging.info("Slept for " + str(slept_for) + 's before archiving started.')
    assert "Archiving          : Started" in archiver_helper.conf_manager_attribute_status(attribute)
    assert "Archiving          : Started" in archiver_helper.evt_subscriber_attribute_status(attribute)
    archiver_helper.stop_archiving(attribute)


def test_configure_attribute(configuration_manager, event_subscriber, attribute, strategy,value):
    attribute = attribute
    sleep_time = 20
    max_retries = 3
    total_slept = 0
    for x in range(0, max_retries):
        try:
            ApiUtil.cleanup()
            configure_attribute(attribute, configuration_manager, event_subscriber, strategy , value)
            break
        except DevFailed as df:
            logging.error("configure_attribute exception: " + str(sys.exc_info()))
            try:
                deviceAdm = DeviceProxy(CM_SERVER)
                deviceAdm.RestartServer()
            except:
                logging.error("reset_conf_manager exception: " + str(sys.exc_info()[0]))
            if (x == (max_retries - 1)):
                raise df

        sleep(sleep_time)
        total_slept += 1

    if (total_slept > 0):
        logging.info("Slept for " + str(total_slept * sleep_time) + 's for the test configuration!')


@pytest.mark.post_deployment
@pytest.mark.skamid
@pytest.mark.skalow
@pytest.mark.parametrize(
    "attribute, strategy, value", [("sys/tg_test/1/double_scalar", "SetPeriodEvent",2000),
                            ("ska_mid/tm_central/central_node/state", "SetCodePushedEvent",True),
                            ("ska_mid/tm_central/central_node/healthstate", "SetRelativeEvent",2.0),
                            ("ska_mid/tm_central/central_node/telescopestate", "SetAbsoluteEvent",3.0)
                            ])
def test_config_attribute(attribute, strategy,value):
    test_configure_attribute(CONF_MANAGER, EVENT_SUBSCRIBER, attribute, strategy, value)
