"""Test for XTP-1561"""
import os
import logging
import time

import pytest
import tango

from pytest_bdd import scenario, given, when, then
from assertpy import assert_that
from ska.skuid.client import SkuidClient
from ska.scripting.domain import SubArray
from oet.command import RemoteScanIdGenerator
from ska.scripting import observingtasks

from resources.test_support.controls import (
    set_telescope_to_standby,
    set_telescope_to_running,
    telescope_is_in_standby,
    take_subarray,
)
from resources.test_support.helpers import resource

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True, scope="module")
def clean_up_telescope(request):
    """Release the subarray resources and set telescope to standby"""

    def put_telescope_to_standby():
        take_subarray(1).and_end_sb_when_ready().and_release_all_resources()
        set_telescope_to_standby()

    request.addfinalizer(put_telescope_to_standby)


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


@pytest.mark.skamid
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
def telescope_is_runnnig():
    if not telescope_is_in_standby():
        set_telescope_to_standby()
    assert telescope_is_in_standby()
    logger.info("Starting up telescope")
    set_telescope_to_running()


@given("the SKUID_URL environment variable has been set")
def check_skuid_url():
    if "SKUID_URL" not in os.environ:
        kube_ns = os.environ.get("KUBE_NAMESPACE", "integration")
        helm_release = os.environ.get("HELM_RELEASE", "test")
        skuid_ns = f"skuid-skuid-{kube_ns}-{helm_release}.{kube_ns}.svc.cluster.local:9870"
        os.environ["SKUID_URL"] = skuid_ns


@given("a scan ID has been retrieved prior to the scan")
def scan_ID_store():
    """Set up the ScanIDStore and increment the scan ID a few times so we don't accidentally get 0"""
    store = ScanIDStore()
    for _ in range(5):
        store.get_next_id()
    return store


@given("Subarray is configured successfully")
def subarray_configure(scan_ID_store):
    """Configure the subarray"""
    dp = tango.DeviceProxy("mid_sdp/elt/subarray_1")
    dp.subscribe_event("scanID", tango.EventType.CHANGE_EVENT, scan_ID_store.callback)

    # Configure for scan
    _, sdp_block = take_subarray(1).to_be_composed_out_of(2)
    take_subarray(1).and_configure_scan_by_file(sdp_block)
    assert_that(resource("ska_mid/tm_subarray_node/1").get("receptorIDList")).is_equal_to((1, 2))
    assert_that(resource("mid_csp/elt/subarray_01").get("assignedReceptors")).is_equal_to((1, 2))


@when("I call the execution of the scan command for duration of 6 seconds")
def do_scan(monkeypatch):
    """Monkeypatching the SCAN_ID_GENERATOR to ensure that the RemoteScanIdGenerator will
    be used"""
    monkeypatch.setattr(
        observingtasks,
        "SCAN_ID_GENERATOR",
        RemoteScanIdGenerator(os.environ["SKUID_URL"]),
        raising=True,
    )
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
