import json
import tempfile
import random
import os

import pytest

from datetime import date
from pathlib import Path

from skuid.client import SkuidClient
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
from oet.domain import SKAMid, SubArray
from resources.test_support.helpers import (
    resource,
    watch,
    take_subarray,
    restart_subarray,
)

KUBE_NAMESPACE = os.environ.get("KUBE_NAMESPACE", "integration")
HELM_RELEASE = os.environ.get("HELM_RELEASE", "test")
SKUID_URL = f"skuid-skuid-{KUBE_NAMESPACE}-{HELM_RELEASE}.{KUBE_NAMESPACE}.svc.cluster.local:9870"
SUBARRAY_CONF_FILE = (
    "/app/skampi/post-deployment/resources/test_data/polaris_b1_no_cam.json"
)


def get_next_scan_id_from_service():
    """Use the skuid service to retrieve a scan ID"""
    client = SkuidClient(SKUID_URL)
    return client.fetch_scan_id()


@pytest.fixture(scope="module")
def pre_test_scan_id(request, autouse=True):
    """Keep the 'before' scan ID"""
    return get_next_scan_id_from_service()


@pytest.fixture(scope="module")
def add_teardown(request, autouse=True):
    """
    Add a finalizer to ensure we always put the subarray back in a defined
    state regardless of test outcome.
    """

    def release():
        if resource("ska_mid/tm_subarray_node/1").get("obsState") == "IDLE":
            SubArray(1).deallocate()
        if resource("ska_mid/tm_subarray_node/1").get("obsState") == "READY":
            SubArray(1).end_sb()
            SubArray(1).deallocate()
        if resource("ska_mid/tm_subarray_node/1").get("obsState") == "CONFIGURING":
            restart_subarray(1)
        SKAMid().standby()

    request.addfinalizer(release)


@pytest.fixture(scope="module")
def subarray_config(request):
    conf_data = Path(SUBARRAY_CONF_FILE).read_text()
    conf_json = json.loads(conf_data)
    today = date.today().strftime("%Y%m%d")
    random_id = random.choice(range(1, 10000))
    conf_json["sdp"]["configure"][0]["id"] = f"realtime-{today}-{random_id}"
    return conf_json


# @pytest.mark.xfail
@pytest.mark.timeout(60)
@scenario("../../features/scan_id.feature", "OET requests a scan ID")
def test_request_scan_id():
    """Test scan ID."""


@given("I am accessing the console interface for the OET")
def start_up():
    """Start up the telescope"""
    SKAMid().start_up()


@given("Sub-array is resourced")
def assign():
    """Assign resources to sub-array"""
    watch_receptor_id_list = watch(
        resource("ska_mid/tm_subarray_node/1")
    ).for_a_change_on("receptorIDList")
    take_subarray(1).to_be_composed_out_of(4)
    watch_receptor_id_list.wait_until_value_changed()


@when("I call the configure scan execution instruction")
def configure(subarray_config):
    with tempfile.NamedTemporaryFile(mode="w") as fp:
        fp.write(json.dumps(subarray_config))
        fp.seek(0)
        SubArray(1).configure_from_file(fp.name)


@then("Sub-array is in READY state")
def check_state():
    """Ensure that the sub-array is in READY state"""
    assert_that(resource("ska_mid/tm_subarray_node/1").get("obsState")).is_equal_to(
        "READY"
    )
    assert_that(resource("mid_csp/elt/subarray_01").get("obsState")).is_equal_to(
        "READY"
    )
    assert_that(resource("mid_sdp/elt/subarray_1").get("obsState")).is_equal_to("READY")


@then("Sub-array reports scan ID")
def check_scan_id(pre_test_scan_id):
    """Ensure that scan ID is as expected and has propagated through sub-array
    """
    scan_id_used = int(resource("ska_mid/tm_subarray_node/1").get("scanID"))
    post_test_scan_id = get_next_scan_id_from_service()
    assert_that(post_test_scan_id > scan_id_used > pre_test_scan_id)
