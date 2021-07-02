import enum
import logging
import time
from multiprocessing import Process, Queue, Event
from os import environ

from oet.procedure.application.restclient import RestClientUI
from ska.cdm.messages.central_node.assign_resources import AssignResourcesRequest
from ska.cdm.schemas import CODEC as cdm_CODEC
from ska.scripting.domain import SubArray

from resources.test_support.helpers import resource
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


class Subarray:
    """
    Subarray is an abstraction of a TMC SubArrayNode Tango device. It is used
    to monitor the device's obsState attribute which should change in response
    to the various commands sent by the observing scripts.
    """

    def __init__(self, device):
        self.resource = resource(device)

    @property
    def obsstate(self):
        return self.resource.get('obsState')

    def obsstate_is(self, obsstate):
        return self.obsstate == obsstate


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
    def __init__(self, device: Subarray):
        # subarray tango device abstraction
        self.device = device
        # mp event that is set when shutdown is called
        self.shutdown_called = Event()
        # shared queue onto which obsState transitions are added
        self.results: Queue = Queue()
        # mp Process that will subscribe to events and add them to results
        self.proc = Process(
            target=self.track_obsstates,
            args=(self.device, self.results, self.shutdown_called)
        )

    def start_recording(self):
        """
        Start recording obsState transitions.
        """
        # start track_obstates, which will run in a new Python child process
        self.proc.start()

    def stop_recording(self):
        self.shutdown_called.set()
        self.proc.join()

    def track_obsstates(
            self,
            device: Subarray,
            obsstate_q: Queue,
            shutdown_called: Event
    ):
        LOGGER.info("STATE MONITORING: Started Tracking")
        last_state = device.obsstate
        obsstate_q.put(last_state)
        while not shutdown_called.is_set():
            current_state = device.obsstate
            if current_state != last_state:
                LOGGER.info(
                    f"STATE MONITORING: State changed: {last_state} -> {current_state}"
                )
                obsstate_q.put(current_state)
                last_state = current_state
        LOGGER.info("STATE MONITORING: Stopped Tracking")

    def state_transitions_match(self, expected_states) -> bool:
        """
        Check that the device passed through the expected
        obsState transitions. This has been being monitored
        on a separate process in the background.

        The method deliberately pauses at the start to allow TMC time
        to complete any operation still in progress.
        """
        time.sleep(PAUSE_AT_END_OF_TASK_COMPLETION_IN_SECS)

        self.stop_recording()

        recorded_states = list()
        while self.results.qsize() != 0:
            recorded_states.append(self.results.get())

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
