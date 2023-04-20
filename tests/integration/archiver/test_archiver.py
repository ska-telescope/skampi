# -*- coding: utf-8 -*-
"""
Test archiver
"""
import logging
import sys
from time import sleep

import pytest

# pylint: disable=E0401
from archiver_helper import ArchiverHelper
from tango import ApiUtil, DevFailed, DeviceProxy


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
def test_init():
    logging.info("Init test archiver")
    archiver_helper = ArchiverHelper()
    archiver_helper.start_archiving()


def configure_attribute(attribute):
    archiver_helper = ArchiverHelper()
    archiver_helper.attribute_add(attribute, 100, 300)
    archiver_helper.start_archiving()
    slept_for = archiver_helper.wait_for_start(attribute)
    logging.info("Slept for " + str(slept_for) + "s before archiving started.")
    assert "Archiving          : Started" in archiver_helper.conf_manager_attribute_status(
        attribute
    )
    assert "Archiving          : Started" in archiver_helper.evt_subscriber_attribute_status(
        attribute
    )
    archiver_helper.stop_archiving(attribute)


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
def test_configure_attribute():
    attribute = "sys/tg_test/1/double_scalar"
    sleep_time = 20
    max_retries = 3
    total_slept = 0
    for x in range(0, max_retries):
        try:
            ApiUtil.cleanup()
            configure_attribute(attribute)
            break
        except DevFailed as df:
            logging.error(f"configure_attribute exception: {sys.exc_info()}")
            try:
                deviceAdm = DeviceProxy("dserver/hdbppcm-srv/01")
                deviceAdm.RestartServer()
            except Exception:
                logging.error(f"reset_conf_manager exception: {sys.exc_info()[0]}")
            if x == (max_retries - 1):
                raise df

        sleep(sleep_time)
        total_slept += 1

    if total_slept > 0:
        logging.info("Slept for {}s for the test configuration!".format(total_slept * sleep_time))
