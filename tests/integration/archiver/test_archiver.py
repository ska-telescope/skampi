# -*- coding: utf-8 -*-
"""
Test archiver
"""
import logging
import os

import pytest

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


def configure_attribute(
    attribute, configuration_manager, event_subscriber, strategy, polling_period, value
):
    archiver_helper = ArchiverHelper(configuration_manager, event_subscriber)
    archiver_helper.start_archiving(attribute, strategy, polling_period, value)
    slept_for = archiver_helper.wait_for_start(attribute)
    logging.info("Slept for " + str(slept_for) + "s before archiving started.")
    assert "Archiving          : Started" in archiver_helper.conf_manager_attribute_status(
        attribute
    )
    assert "Archiving          : Started" in archiver_helper.evt_subscriber_attribute_status(
        attribute
    )
    archiver_helper.stop_archiving(attribute)


@pytest.mark.post_deployment
@pytest.mark.skamid
@pytest.mark.skalow
@pytest.mark.parametrize(
    "attribute, strategy, polling_period, value",
    [
        ("sys/tg_test/1/double_scalar", "SetPeriodEvent", 1000, 2000),
        (f"ska_{CONFIG}/tm_central/central_node/state", "SetCodePushedEvent", None, True),
        (f"ska_{CONFIG}/tm_central/central_node/healthstate", "SetRelativeEvent", None, 2.0),
        (f"ska_{CONFIG}/tm_central/central_node/telescopestate", "SetAbsoluteEvent", None, 3.0),
    ],
)
def test_config_attribute(attribute, strategy, polling_period, value):
    configure_attribute(attribute, CONF_MANAGER, EVENT_SUBSCRIBER, strategy, polling_period, value)
