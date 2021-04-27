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

from skallop.mvp_fixtures import subarray_composition as sub_comp_fxt
from skallop.mvp_fixtures import subarray_configuration as sub_conf_fxt

from resources.test_support.controls import (
    set_telescope_to_standby,
    set_telescope_to_running,
    telescope_is_in_standby,
    take_subarray,
    restart_subarray,
)
from resources.test_support.helpers import resource

logger = logging.getLogger(__name__)

@pytest.fixture
def subarray_id():
    return 1

@pytest.fixture
def nr_of_dishes():
    return 2

# overrides composed subarray fixture args
@pytest.fixture(name='composed_subarray_args')
def fxt_composed_subarray_args(tmp_path, nr_of_dishes, subarray_id: int):
    # SB_config == "standard"
    composition = sub_comp_fxt.conf_types.CompositionByFile(
        tmp_path, sub_comp_fxt.conf_types.FileCompositionType.standard
    )
    return sub_comp_fxt.Args(
        subarray_id=subarray_id,
        receptors=list(range(1, nr_of_dishes + 1)),
        composition=composition,
    )

# overrides skallop.mvp_fixtures.subarray_composition.configured_subarray_args
@pytest.fixture(name='configured_subarray_args')
def fxt_configured_subarray_args(tmp_path, composed_subarray_args: sub_comp_fxt.Args):
    configuration = sub_conf_fxt.conf_types.ConfigurationByFile(
        tmp_path,
        sub_conf_fxt.conf_types.FileConfigurationType.standard,
        composed_subarray_args.composition.metadata,
    )
    return sub_conf_fxt.Args(
        subarray_id= composed_subarray_args.subarray_id,
        receptors=composed_subarray_args.receptors,
        configuration=configuration,
    )


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


@given("a scan ID has been retrieved prior to the scan")
def scan_ID_store():
    """Set up the ScanIDStore and increment the scan ID a few times so we don't accidentally get 0"""
    store = ScanIDStore()
    for _ in range(5):
        store.get_next_id()
    return store


@given("Subarray is configured successfully")
def subarray_configure(scan_ID_store,composed_subarray,configured_subarray):
    """Configure the subarray"""
    dp = tango.DeviceProxy("mid_sdp/elt/subarray_1")
    dp.subscribe_event("scanID", tango.EventType.CHANGE_EVENT, scan_ID_store.callback)



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
