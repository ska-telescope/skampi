import enum
import logging
import threading
import time
from os import environ

from oet.procedure.application.restclient import RestClientUI
from ska_tmc_cdm.messages.central_node.assign_resources import AssignResourcesRequest
from ska_tmc_cdm.schemas import CODEC as cdm_CODEC
from ska.scripting.domain import SubArray
from tango import DeviceProxy, EventType

from resources.test_support.persistance_helping import update_resource_config_file

# OET task completion can occur before TMC has completed its activity - so allow time for the
# last transitions to take place
PAUSE_AT_END_OF_TASK_COMPLETION_IN_SECS = 10

LOGGER = logging.getLogger(__name__)

helm_release = environ.get("HELM_RELEASE", "test")
rest_cli_uri = f"http://oet-rest-{helm_release}:5000/api/v1.0/procedures"
REST_CLIENT = RestClientUI(rest_cli_uri)

def oet_compose_sub():
    cdm_file_path = 'resources/test_data/OET_integration/example_allocate.json'
    LOGGER.info("cdm_file_path :" + str(cdm_file_path))
    update_resource_config_file(cdm_file_path)
    cdm_request_object = cdm_CODEC.load_from_file(AssignResourcesRequest, cdm_file_path)
    cdm_request_object.dish.receptor_ids = [str(x).zfill(4) for x in range(1, 5)]
    subarray = SubArray(1)
    LOGGER.info("Allocated Subarray is :" + str(subarray))
    return subarray.allocate_from_cdm(cdm_request_object)


class ObsState(enum.Enum):
    """
    Represent the ObsState Tango enumeration
    """
    EMPTY = 0
    RESOURCING = 1
    IDLE = 2
    CONFIGURING = 3
    READY = 4
    SCANNING = 5
    ABORTING = 6
    ABORTED = 7
    RESETTING = 8
    FAULT = 9
    RESTARTING = 10

    def __str__(self):
        """
        Convert enum to string
        """
        # str(ObsState.IDLE) gives 'IDLE'
        return str(self.name)


class ObsStateRecorder:
    """
    ObsStateRecorder is an OET test helper that helps compare SubArrayNode
    obsState transitions to those expected to occur when a script is run.

    This class subscribes to SubArrayNode change events, making a memo of each
    obsState transition that occurs between when state recording starts and
    when state recording stops. This list of recorded obsStates is compared to
    the expected list of obsStates in state_transitions_match. A successful
    test occurs when the expected obsState transitions matches the observed
    obsState transitions, otherwise the test is considered failed.

    ObsStateRecorders are intended to be activated once and cannot be reused
    to record multiple streams of obsState transitions. A RuntimeError will be
    raised if an attempt is made to resume obsState recording.
    """

    def __init__(self, device_url: str):
        """
        Create a new ObsStateRecorder tracking the referenced SubArrayNode.

        :param device_url: Tango FQDN of SubArrayNode to monitor
        """
        # event that is set when recording should start
        self._recording_enabled = threading.Event()
        # shared queue onto which obsState transitions are added
        self.results = []

        # connect to the target device and subscribe to obsState change events
        self.dp = DeviceProxy(device_url)
        self.subscription_id = self.dp.subscribe_event(
            'obsState',
            EventType.CHANGE_EVENT,
            self._cb
        )

    def start_recording(self):
        """
        Start recording obsState transitions.

        This method can be called exactly once. Calling this method after
        stop_recording has been called will raise a RuntimeError.

        :raises RuntimeError: if the caller attempts to resume recording
        """
        if self.subscription_id is None:
            raise RuntimeError(
                'Cannot restart obsState recording on a stopped ObsStateRecorder'
            )

        # the subscription is already established, so just set the event to
        # start recording obstates
        self._recording_enabled.set()
        LOGGER.info("STATE MONITORING: Started tracking")

    def stop_recording(self):
        """
        Stop recording obsState change events, unsubscribing the active callback.
        """
        self._recording_enabled.clear()
        LOGGER.info("STATE MONITORING: Stopped tracking")

        # unsubscribe and delete subscription ID to prevent this instance from
        # being reused
        self.dp.unsubscribe_event(self.subscription_id)
        self.subscription_id = None

    def _cb(self, event):
        """
        Function called by pytango when obsState change event is received
        """
        # discard any events received while recording is disabled
        if not self._recording_enabled:
            return

        # obsstate Enum returned as a numeric ID which we need to translate to name
        enum_id = event.attr_value.value
        enum_name = ObsState(enum_id).name

        LOGGER.info(
            f"STATE MONITORING: State changed: {enum_name}"
        )
        self.results.append(enum_name)

    def state_transitions_match(self, expected_states) -> bool:
        """
        Check that the device passed through the expected
        obsState transitions. This has been being monitored
        on a separate process in the background.

        The method deliberately pauses at the start to allow TMC time
        to complete any operation still in progress.

        stop_recording must be called before calling this method.

        :raises RuntimeError: if called while still recording
        """
        if self._recording_enabled.is_set():
            raise RuntimeError('Cannot compare states while still recording')
        time.sleep(PAUSE_AT_END_OF_TASK_COMPLETION_IN_SECS)

        recorded_states = self.results

        # ignore 'READY' as it can be a transitory state so we don't rely
        # on it being present in the list to be matched
        recorded_states = [i for i in recorded_states if i != 'READY']

        n_expected = len(expected_states)
        n_recorded = len(recorded_states)

        LOGGER.info("STATE MONITORING: Comparing the list of states observed with the expected states")
        LOGGER.debug("STATE MONITORING: Expected states: %s", ','.join(expected_states))
        LOGGER.debug("STATE MONITORING: Recorded states: %s", ','.join(recorded_states))

        if n_expected != n_recorded:
            LOGGER.warning(
                f"STATE MONITORING: Expected {n_expected} states, got {n_recorded}"
            )
            return False

        if expected_states != recorded_states:
            LOGGER.warning("STATE MONITORING: Expected states do not match recorded states")
            return False

        LOGGER.info("STATE MONITORING: All states match")
        return True


class Task:
    def __init__(self, task_id, script, creation_time, state):
        self.task_id = task_id
        self.script = script
        self.creation_time = creation_time
        self.state = state

    def state_is(self, expected):
        return self.state == expected


class ScriptExecutor:
    @staticmethod
    def parse_rest_response_line(line):
        """Split a line from the REST API lines
        into columns

        Args:
            line (string): A line from OET REST CLI response

        Returns:
            task: Task object with task information.
        """
        elements = line.split()
        task = Task(
            task_id=elements[0],
            script=elements[1],
            creation_time=str(elements[2] + ' ' + elements[3]),
            state=elements[4])
        return task

    @staticmethod
    def parse_rest_response(resp):
        """Split the response from the REST API lines
        into columns

        Args:
            resp (string): Response from OET REST CLI

        Returns:
            [task]: List Task objects.
        """
        task_list = []
        lines = resp.splitlines()
        del lines[0:2]
        for line in lines:
            task = ScriptExecutor.parse_rest_response_line(line)
            task_list.append(task)
        return task_list

    @staticmethod
    def parse_rest_start_response(resp):
        """ Split the response from the REST API start
        command into columns.

        This needs to be done separately from other OET REST
        Client responses because starting a script returns a
        Python Generator object instead of a static string.

        Args:
            resp (Generator): Response from OET REST CLI start

        Returns:
            task: Task object with information on the started task.
        """
        for line in resp:
            # Only get line with script details (ignore header lines)
            if 'RUNNING' in line:
                return ScriptExecutor.parse_rest_response_line(line)
        return None

    @staticmethod
    def wait_for_script_to_complete(task_id, timeout):
        """
        Wait until the script with the given ID is no longer
        running.

        Args:
            task_id (str): ID of the script on the task list
            timeout (int): timeout (~seconds) how long to wait
            for script to complete

        Returns:
            task.state: State of the script after completion.
            None if timeout occurs before state changes from RUNNING.
        """
        t = timeout
        while t != 0:
            task = ScriptExecutor().get_script_by_id(task_id)
            if not task.state_is('RUNNING'):
                LOGGER.info("Script state changed from RUNNING to %s", task.state)
                return task.state
            time.sleep(1)
            t -= 1

        LOGGER.info("Timeout occurred (> %d seconds) when waiting for script "
                    "to complete. Stopping script.", timeout)
        ScriptExecutor().stop_script()
        task = ScriptExecutor().get_script_by_id(task_id)
        LOGGER.info("Script state: %s", task.state)
        return task.state

    def create_script(self, script) -> Task:
        resp = REST_CLIENT.create(script, subarray_id=1)
        tasks = ScriptExecutor.parse_rest_response(resp)
        return tasks[0]

    def start_script(self, *script_args) -> Task:
        resp = REST_CLIENT.start(*script_args, listen=False)
        task = ScriptExecutor.parse_rest_start_response(resp)
        return task

    def stop_script(self):
        REST_CLIENT.stop(run_abort=False)

    def list_scripts(self):
        resp = REST_CLIENT.list()
        tasks = ScriptExecutor.parse_rest_response(resp)
        return tasks

    def get_latest_script(self):
        tasks = self.list_scripts()
        return tasks[-1]

    def get_script_by_id(self, task_id):
        tasks = self.list_scripts()
        for task in tasks:
            if task.task_id == task_id:
                return task
        return None

    def execute_script(self, script, *script_run_args, timeout=200):
        """
        Execute the given script using OET REST client.

        Args:
            script (str): Script file to execute
            script_run_args: Arguments to pass to the script when
            the script execution is started
            timeout: Timeout (~seconds) for how long to wait for script
            to complete

        Returns:
            script_final_state: State of the script after completion.
            None if something goes wrong.
        """
        LOGGER.info("Running script %s", script)

        # create script
        created_task = self.create_script(script)

        # confirm that creating the task worked and we have a valid ID
        if not created_task.state_is('CREATED'):
            LOGGER.info("Expected script to be CREATED but instead was %s",
                        created_task.state)
            return None

        # start execution of created script
        started_task = self.start_script(*script_run_args)
        # confirm that it didn't fail on starting
        if not started_task.state_is('RUNNING'):
            LOGGER.info("Expected script to be RUNNING but instead was %s",
                        started_task.state)
            return None

        # If task IDs do not match, wrong script was started
        if created_task.task_id != started_task.task_id:
            LOGGER.info("Script IDs did not match, created script with ID %s but started script with ID %s",
                        created_task.task_id, started_task.task_id)
            return None

        script_final_state = ScriptExecutor.wait_for_script_to_complete(started_task.task_id, timeout)
        return script_final_state
