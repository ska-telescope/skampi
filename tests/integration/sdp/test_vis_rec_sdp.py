"""Visibility receive test."""

# pylint: disable=import-error
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-locals
# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

import contextlib
import json
import logging
import random
import time
from typing import Any, List, Optional
import requests
import os
from datetime import date

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from integration.sdp.vis_receive_utils import (
    wait_for_obs_state,
    compare_data,
    POD_CONTAINER,
    deploy_sender,
    wait_for_pod,
    check_data_present,
    pvc_exists,
    wait_for_predicate,
)

LOG = logging.getLogger(__name__)

RECEIVE_POD = "tests/resources/kubernetes/sdp-test-visibility-receive-pod.yaml"
SENDER_POD = "tests/resources/kubernetes/sdp-test-visibility-sender-pod.yaml"
PVC_NAME = os.environ.get("SDP_DATA_PVC_NAME", "shared")

namespace = os.environ.get("KUBE_NAMESPACE")
namespace_sdp = os.environ.get("KUBE_NAMESPACE_SDP")

TIMEOUT_ASSIGNRES = 120.0

# Translations for the obsState attribute. The Tango clients return an integer
# value, so this is used to convert the value into a name.
TRANSLATIONS = {
    "obsState": {
        0: "EMPTY",
        1: "RESOURCING",
        2: "IDLE",
        3: "CONFIGURING",
        4: "READY",
        5: "SCANNING",
        6: "ABORTING",
        7: "ABORTED",
        8: "RESETTING",
        9: "FAULT",
        10: "RESTARTING",
    }
}

# scenarios("visibility_receive.feature")

@pytest.mark.skalow
@pytest.mark.sdp
@scenario(
    "features/sdp_visibility_receive.feature",
    "Execute visibility receive script for a single scan (SDP)",
)
def test_visibility_receive_in_low():
    """
    SDP Visibility receive test.

    :param assign_resources_test_exec_settings: Object for assign_resources_test_exec_settings
    """


@pytest.fixture(name="assign_resources_config")
def read_assign_resources_config():
    """
    Read the AssignResources config for visibility receive.

    Substitutes randomly-generated IDs so the test can be run more than once in
    the same instance of SDP. The config is used in more than one step in the
    test, so it must be a fixture.

    """
    config = read_json_data("visibility_receive.json")

    config["execution_block"]["eb_id"] = create_id("eb")
    for pblock in config["processing_blocks"]:
        pblock["pb_id"] = create_id("pb")
        pb_params = pblock["parameters"]
        pb_params["pvc"]["name"] = "shared"
        for init_container in pb_params["plasma_parameters"]["initContainers"]:
            init_container["volumeMounts"][0]["name"] = "shared"
        pb_params["plasma_parameters"]["extraContainers"][0]["volumeMounts"][
            1
        ]["name"] = "shared"

    return config


@pytest.fixture
def dataproduct_directory(assign_resources_config):
    """
    The directory where output files will be written.

    :param assign_resources_config: AssignResources configuration
    """
    eb_id = assign_resources_config["execution_block"]["eb_id"]
    pb_id = assign_resources_config["processing_blocks"][0]["pb_id"]
    return f"/product/{eb_id}/ska-sdp/{pb_id}"


@pytest.fixture(name="vis_receive_script")
def run_vis_receive_script(
    subarray_device, k8s_element_manager, assign_resources_config
):
    """
    Start the visibility receive script and end it after the test.

    This uses the k8s_element_manager fixture to ensure the script is ended
    before the PVCs are removed.

    :param subarray_device: SDP subarray device client
    :param k8s_element_manager: Kubernetes element manager
    :param assign_resources_config: AssignResources configuration

    """

    # Start the script

    LOG.info("Calling AssignResources")
    subarray_device.execute_command(
        "AssignResources", argument=json.dumps(assign_resources_config)
    )

    yield

    LOG.info("Calling End")
    subarray_device.execute_command("End")
    wait_for_obs_state(subarray_device, "IDLE", timeout=30)

    # End the script
    LOG.info("Calling ReleaseAllResources")
    subarray_device.execute_command("ReleaseAllResources")


@pytest.fixture
def subarray_scan(subarray_device):
    """
    Execute a scan.

    :param subarray_device: SDP subarray device client

    """
    timeout = 30
    configure_command = read_command_argument("Configure")
    scan_command = read_command_argument("Scan")

    @contextlib.contextmanager
    def subarray_do_scan(scan_id, scan_type_id, prev_scan_type=None):
        # If previous scan_type is same as the current scan type
        # then don't need to run Configure command
        if scan_type_id != prev_scan_type:
            # Configure
            LOG.info("Calling Configure(scan_type=%s)", scan_type_id)
            configure_command["scan_type"] = scan_type_id
            subarray_device.execute_command(
                "Configure",
                argument=json.dumps(configure_command),
            )
            wait_for_obs_state(subarray_device, "READY", timeout=timeout)

        # Scan
        LOG.info("Calling Scan(scan_id=%d)", scan_id)
        scan_command["scan_id"] = scan_id
        subarray_device.execute_command("Scan", json.dumps(scan_command))
        wait_for_obs_state(subarray_device, "SCANNING", timeout=timeout)

        try:
            yield
        finally:
            # Revert back to IDLE
            LOG.info("Calling EndScan")
            subarray_device.execute_command("EndScan")
            wait_for_obs_state(subarray_device, "READY", timeout=timeout)

    return subarray_do_scan


# -----------
# Given steps
# -----------


@given("I connect to an SDP subarray", target_fixture="subarray_device")
def connect_to_subarray():
    """
    Connect to the subarray device.

    :param context: context for the tests
    :returns: SDP subarray device client

    """

    job_id = os.getenv("CI_JOB_ID")
    tango_url = f"http://tangogql-ska-tango-tangogql-test-low-{job_id}.{namespace}:5004"
    subarray = f"ska-sdp/subarray/01"
    return TangoClientGQL(
        tango_url, subarray, translations=TRANSLATIONS
    )


@given(parsers.parse("obsState is {obs_state:S}"))
def set_obs_state(subarray_device, obs_state):
    """
    Set the obsState to the desired value.

    This function sets the device state to ON.

    :param subarray_device: SDP subarray device client
    :param obs_state: desired obsState

    """

    current = (
        subarray_device.get_attribute("State"),
        subarray_device.get_attribute("obsState"),
    )
    target = ("ON", obs_state)
    commands = transition_commands(current, target)

    for command in commands:
        call_command(subarray_device, command)
        if command == "AssignResources":
            wait_for_obs_state(subarray_device, "IDLE", timeout=TIMEOUT_ASSIGNRES)

    assert subarray_device.get_attribute("State") == "ON"
    assert subarray_device.get_attribute("obsState") == obs_state


@given("the test volumes are present and the test data are downloaded")
def local_volume(k8s_element_manager, fxt_k8s_cluster):
    """
    Check if the local volumes are present and the data
    have been successfully downloaded.

    :param k8s_element_manager: Kubernetes element manager
    :param fxt_k8s_cluster: fixture to use a KUBECONFIG file (if present),
                for performing k8s commands (see unit.test_cluster_k8s)
    """  # noqa: DAR401
    if namespace is None or namespace_sdp is None:
        raise ValueError("Env var KUBE_NAMESPACE or KUBE_NAMESPACE_SDP is not defined")

    receive_pod = "sdp-receive-data"
    sender_pod = "sdp-sender-data"
    data_container = POD_CONTAINER

    LOG.info("Check for existing PVC")
    assert pvc_exists(PVC_NAME, namespace_sdp), f"PVC in {namespace_sdp} doesn't exist"
    assert pvc_exists(PVC_NAME, namespace), f"PVC in {namespace} doesn't exist"

    LOG.info("Create Pod for receiver and sender")
    k8s_element_manager.create_pod(receive_pod, namespace_sdp, PVC_NAME)
    k8s_element_manager.create_pod(sender_pod, namespace, PVC_NAME)

    ms_file_mount_location = "/mnt/data/AA05LOW.ms/"

    # Check if the measurement set has been download into pods
    def _wait_for_receive_data():
        receiver_result = check_data_present(
            receive_pod,
            data_container,
            namespace_sdp,
            ms_file_mount_location,
        )
        if receiver_result.returncode == 0:
            LOG.info("MS data downloaded into receive pod")
            return True
        return False

    def _wait_for_sender_data():
        sender_result = check_data_present(
            sender_pod,
            data_container,
            namespace,
            ms_file_mount_location,
        )
        if sender_result.returncode == 0:
            LOG.info("MS data downloaded into sender pod")
            return True
        return False

    wait_for_predicate(_wait_for_receive_data, "MS data not present in volume.", timeout=100)()
    wait_for_predicate(_wait_for_sender_data, "MS data not present in volume.", timeout=100)()

    LOG.info("PVCs are present, pods created, and data downloaded successfully")


@given("I deploy the visibility receive script")
def deploy_script(
    vis_receive_script, subarray_device, assign_resources_config
):
    """
    Deploy visibility receive script.

    This uses the vis_receive_script fixture to automatically end the
    script when the test is finished.

    :param vis_receive_script: visibility receive script fixture
    :param context: context for the tests
    :param subarray_device: SDP subarray device client
    :param assign_resources_config: AssignResources configuration

    """
    wait_for_obs_state(subarray_device, "IDLE", timeout=TIMEOUT_ASSIGNRES)

    receive_addresses = json.loads(
        subarray_device.get_attribute("receiveAddresses")
    )
    # Get the DNS hostname from receive addresses attribute
    host = receive_addresses["target:a"]["vis0"]["host"][0][1]
    receiver_pod_name = host.split(".")[0]

    # Check if the receiver is running
    LOG.info("Waiting for receive pod to be 'Running'")
    assert wait_for_pod(
        receiver_pod_name,
        namespace_sdp,
        "Running",
        timeout=600,
        pod_condition="Ready",
    )

    LOG.info("Receive pod is running. Checking receive addresses.")
    receive_addresses_expected = f"{receiver_pod_name}.receive.{namespace_sdp}"

    assert host == receive_addresses_expected


# ----------
# When steps
# ----------


@when("SDP is commanded to capture data from a scan")
def run_scans(
    subarray_device, subarray_scan, k8s_element_manager
):
    """
    Run a sequence of scans.

    :param context: context for the tests
    :param telescope: the SKA telescope for which to emulate data sending
    :param subarray_device: SDP subarray device client
    :param subarray_scan: scan fixture
    :param k8s_element_manager: Kubernetes element manager

    """
    receive_addresses = json.loads(
        subarray_device.get_attribute("receiveAddresses")
    )

    host = receive_addresses["target:a"]["vis0"]["host"][0][1]
    with subarray_scan(1, "target:a"):
        deploy_sender(
            host,
            1,
            k8s_element_manager,
        )


# ----------
# Then steps
# ----------


@then("the data received matches with the data sent")
def check_measurement_set(
    dataproduct_directory, k8s_element_manager
):
    """
    Check the data received are same as the data sent.

    :param dataproduct_directory: The directory where outputs are written
    :param k8s_element_manager: Kubernetes element manager
    :param sut_settings: SUT settings fixture
    """
    # Wait 10 seconds before checking the measurement.
    # This gives enough time for the receiver for finish writing the data.
    time.sleep(10)

    receive_pod = "sdp-receive-data"
    data_container = POD_CONTAINER

    # Add data product directory to k8s element manager for cleanup
    parse_dir = dataproduct_directory.index("ska-sdp")
    data_eb_dir = dataproduct_directory[:parse_dir]
    k8s_element_manager.output_directory(
        data_eb_dir,
        receive_pod,
        data_container,
        namespace_sdp,
    )

    result = compare_data(
        receive_pod,
        data_container,
        namespace_sdp,
        f"{dataproduct_directory}/output.scan-1.ms",
    )
    assert result.returncode == 0
    LOG.info("Data sent matches the data received")


# ====================

"""TangoGQL-based client."""

class DevError(Exception):
    """
    Tango device error exception.

    :param desc: description of exception
    :param reason: reason for exception
    """

    def __init__(self, desc=None, reason=None):
        super().__init__()
        self.desc = desc
        self.reason = reason


class TangoClient:
    """
    Base class for Tango device clients.

    :param device: name of device
    :param translations: optional translations for attribute values
    """

    def __init__(self, device: str, translations: Optional[dict] = None):
        self._device = device
        self._translations = translations
        self._exception = None

    @property
    def exception(self) -> Optional[Exception]:
        """Get the stored exception."""
        return self._exception

    def clear_exception(self):
        """Clear the stored exception."""
        self._exception = None

    def _translate_attribute(self, attribute: str, value: Any) -> Any:
        """
        Translate attribute value.

        :param attribute: attribute name
        :param value: attribute value
        :returns: translated attribute value

        """
        if self._translations and attribute in self._translations:
            value = self._translations[attribute][value]
        return value

    def get_commands(self) -> Optional[List[str]]:
        """
        Get list of commands from device.

        :returns: list of command names

        """
        raise NotImplementedError()

    def get_attribute(self, attribute: str) -> Any:
        """
        Get value of device attribute.

        :param attribute: name of attribute
        :returns: value of attribute

        """
        raise NotImplementedError()

    def execute_command(
        self, command: str, argument: Optional[str] = None
    ) -> Any:
        """
        Execute command.

        :param command: name of command
        :param argument: optional argument for command
        :returns: return value of command

        """
        raise NotImplementedError()


class GraphQLClient:
    """
    Simple GraphQL client.

    :param url: URL of GraphQL endpoint
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, url: str):
        self._url = url

    def execute(self, query: str, variables: dict = None):
        """
        Execute query on GraphQL server.

        :param query: query to execute (can be query or mutation)
        :param variables: variables for query

        """
        data = {"query": query, "variables": variables}
        response = requests.post(url=self._url, json=data, timeout=10.0)
        response.raise_for_status()
        return response.json()


class TangoClientGQL(TangoClient):
    """
    Client for a Tango device using TangoGQL.

    :param url: URL of TangoGQL server
    :param device: name of device
    :param translations: optional translations for attribute values
    """

    query_get_commands = """
        query GetCommands($device: String!) {
            device(name: $device) {
                commands {
                    name
                }
            }
        }
    """

    query_fetch_attribute_names = """
        query FetchAttributeNames($device: String!) {
          device(name: $device) {
            attributes {
              name
              label
              dataformat
              datatype
            }
          }
        }
    """

    query_get_attribute = """
        query GetAttribute($device: String!, $attribute: String!) {
            device(name: $device) {
                attributes(pattern: $attribute) {
                    value
                }
            }
        }
    """

    mutation_execute_command = """
        mutation ExecuteCommand($device: String!, $command: String!, $argument: ScalarTypes) {
            executeCommand(device: $device, command: $command, argin: $argument) {
                ok
                message
                output
            }
        }
    """  # noqa: E501

    def __init__(
        self, url: str, device: str, translations: Optional[dict] = None
    ):
        super().__init__(device, translations=translations)
        self._client = GraphQLClient(f"{url}/db")

    def get_commands(self) -> Optional[List[str]]:
        """
        Get list of commands from device.

        :returns: list of command names

        """
        variables = {"device": self._device}
        response = self._client.execute(self.query_get_commands, variables)
        commands = [
            command["name"]
            for command in response["data"]["device"]["commands"]
        ]
        if not commands:
            self._exception = DevError(
                desc=f"Device {self._device} is not exported",
                reason="API_DeviceNotExported",
            )
        return commands

    def fetch_attribute_names(self) -> Optional[List[str]]:
        """
        Get list of attributes from device.

        :returns: list of attribute names

        """
        variables = {"device": self._device}
        response = self._client.execute(
            self.query_fetch_attribute_names, variables
        )
        attributes = [
            attribute["name"]
            for attribute in response["data"]["device"]["attributes"]
        ]
        if not attributes:
            self._exception = DevError(
                desc=f"Device {self._device} is not exported",
                reason="API_DeviceNotExported",
            )
        return attributes

    def get_attribute(self, attribute: str) -> Any:
        """
        Get value of device attribute.

        :param attribute: name of attribute
        :returns: value of attribute

        """
        variables = {"device": self._device, "attribute": attribute}
        response = self._client.execute(self.query_get_attribute, variables)
        attributes = response["data"]["device"]["attributes"]
        if attributes:
            value = attributes[0]["value"]
            if self._translations and attribute in self._translations:
                value = self._translations[attribute][value]
        else:
            value = None
            self._exception = DevError(
                desc=f"Device {self._device} is not exported",
                reason="API_DeviceNotExported",
            )
        return value

    def execute_command(
        self, command: str, argument: Optional[str] = None
    ) -> Any:
        """
        Execute command.

        :param command: name of command
        :param argument: optional argument for command
        :returns: return value of command

        """
        variables = {
            "device": self._device,
            "command": command,
            "argument": argument,
        }
        response = self._client.execute(
            self.mutation_execute_command, variables=variables
        )
        if not response["data"]["executeCommand"]["ok"]:
            desc, reason = response["data"]["executeCommand"]["message"]
            self._exception = DevError(desc=desc, reason=reason)
        return response["data"]["executeCommand"]["output"]


# =================


def transition_commands(current, target):
    """
    Get list of commands to transition from current state to target state.

    :param current: tuple of current state and obs_state
    :param target: tuple of target state and obs_state
    :returns: list of commands

    """
    # Mapping of state and obs_state to state number
    state_number = {
        ("OFF", "EMPTY"): 0,
        ("ON", "EMPTY"): 1,
        ("ON", "IDLE"): 2,
        ("ON", "READY"): 3,
        ("ON", "SCANNING"): 4,
    }
    # Command to transition to previous state number
    command_prev = [None, "Off", "ReleaseResources", "End", "EndScan"]
    # Command to transition to next state number
    command_next = ["On", "AssignResources", "Configure", "Scan", None]

    current_number = state_number[current]
    target_number = state_number[target]

    if target_number < current_number:
        commands = [
            command_prev[i] for i in range(current_number, target_number, -1)
        ]
    elif target_number > current_number:
        commands = [
            command_next[i] for i in range(current_number, target_number)
        ]
    else:
        commands = []

    return commands


def read_json_data(filename):
    """
    Read data from JSON file in the data directory.

    :param filename: name of the file to read

    """
    path = os.path.join("tests", "resources", "subarray-json", filename)
    with open(path, "r", encoding="utf-8") as file_n:
        data = json.load(file_n)
    return data


def create_id(prefix):
    """
    Create an ID with the given prefix.

    The ID will contain today's date and a random 5-digit number.

    :param prefix: the prefix

    """
    generator = "test"
    today = date.today().strftime("%Y%m%d")
    number = random.randint(0, 99999)
    return f"{prefix}-{generator}-{today}-{number:05d}"


def read_command_argument(name):
    """
    Read command argument from JSON file.

    :param name: name of command

    """
    config = read_json_data(f"command_{name}.json")

    if name == "AssignResources":
        # Insert new IDs into configuration
        config["execution_block"]["eb_id"] = create_id("eb")
        for pblock in config["processing_blocks"]:
            pblock["pb_id"] = create_id("pb")

    return config


def call_command(subarray_device, command):
    """
    Call a device command.

    :param subarray_device: SDP subarray device client
    :param command: name of command to call

    """
    # Check command is present
    assert command in subarray_device.get_commands()
    # Get the command argument
    if command in [
        "AssignResources",
        "ReleaseResources",
        "Configure",
        "Scan",
    ]:
        config = read_command_argument(command)
        argument = json.dumps(config)
    else:
        argument = None

    # Remember the EB ID
    if command == "AssignResources":
        subarray_device.eb_id = config["execution_block"]["eb_id"]
    elif command == "End":
        subarray_device.eb_id = None

    # Call the command
    subarray_device.execute_command(command, argument=argument)
