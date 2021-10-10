"""Test for XTP-1561"""
import os
import logging
import time

import pytest


import tango

from pytest_bdd import scenario, given, when, then
from assertpy import assert_that
from ska_ser_skuid.client import SkuidClient
from ska.scripting.domain import SubArray
from oet.command import RemoteScanIdGenerator
from ska.scripting import observingtasks
from ska_ser_skallop.mvp_fixtures.env_handling import ExecEnv
from ska_ser_skallop.mvp_fixtures.context_management import SubarrayContext
from ska_ser_skallop.mvp_control.event_waiting import set_to_wait, wait



logger = logging.getLogger(__name__)


class ScanIDStore:
    """This stores the information needed to run the tests and is passed around BDD
    steps via fixture
    """

    def __init__(self) -> None:
        self.current_id = -1
        self.skuid_client = SkuidClient(os.environ["SKUID_URL"])
        self.callback = tango.utils.EventCallback()

    def get_next_id(self):
        """Get the next scan ID from skuid"""
        self.current_id = self.skuid_client.fetch_scan_id()
        return self.current_id

def set_entry_point(exec_env: ExecEnv):
    exec_env.entrypoint = "tmc"

@pytest.mark.skamid
@pytest.mark.quarantine
@scenario(
    "XTP-1561.feature",
    (
        "TMC coordinates observational scan and SDP uses the scan ID as provided by"
        " the skuid service"
    ),
)
def test_scan_id():
    pass


@given("a running telescope")
def telescope_is_runnnig(running_telescope):
    pass


@given("the SKUID_URL environment variable has been set")
def check_skuid_url():
    assert "SKUID_URL" in os.environ


@given("a scan ID has been retrieved prior to the scan",target_fixture='scan_ID_store')
def scan_ID_store():
    """Set up the ScanIDStore and increment the scan ID a few times so we don't accidentally get 0"""
    store = ScanIDStore()
    for _ in range(5):
        store.get_next_id()
    return store


@given("Subarray is configured successfully")
def subarray_configure(scan_ID_store,configured_subarray):
    """Configure the subarray"""
    dp = tango.DeviceProxy("mid_sdp/elt/subarray_1")
    dp.subscribe_event("scanID", tango.EventType.CHANGE_EVENT, scan_ID_store.callback)



@when("I call the execution of the scan command for duration of 6 seconds")
def do_scan(monkeypatch, configured_subarray: SubarrayContext,):
    """Monkeypatching the SCAN_ID_GENERATOR to ensure that the RemoteScanIdGenerator will
    be used"""
    monkeypatch.setattr(
        observingtasks,
        "SCAN_ID_GENERATOR",
        RemoteScanIdGenerator(os.environ["SKUID_URL"]),
        raising=True,
    )
    board = set_to_wait.set_waiting_for_scanning_to_complete(configured_subarray.id, configured_subarray.receptors)
    with wait.wait_for(board, timeout=60):
        SubArray(1).scan()


@then(
    "the scanID used by SDP has a value equal to the last ID that was retrieved prior to the scan plus one"
)
def check_correct_id_used(scan_ID_store):
    """Check the scanID"""
    # Give the change event up to 5s to arrive
    counter = 1
    while len(scan_ID_store.callback.get_events()) < 2:
        if counter == 5:
            break
        logger.info("Waiting for events, only %s so far", len(scan_ID_store.callback.get_events()))
        counter += 1
        time.sleep(1)

    scan_id_after_our_initial_fetch = scan_ID_store.current_id + 1
    scan_ids = [event.attr_value.value for event in scan_ID_store.callback.get_events()]
    logger.info("scanID expected %s, found %s", scan_id_after_our_initial_fetch, scan_ids)
    assert scan_id_after_our_initial_fetch in scan_ids, (
        f"Current scan_ID_store ID {scan_ID_store.current_id}. "
        f"Expected {scan_id_after_our_initial_fetch} in {scan_ids}"
    )
