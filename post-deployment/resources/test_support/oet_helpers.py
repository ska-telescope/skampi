import enum
import logging
from os import environ
import time
from multiprocessing import Process, Manager, Queue

from assertpy import assert_that
# SUT import
from oet.procedure.application.restclient import RestClientUI

from resources.test_support.helpers import resource

# arbitrary number, this only needs to be this big to cover a science scan of several seconds
DEFAUT_LOOPS_DEFORE_TIMEOUT = 10000
# avoids swamping the rest server but short enough to avoid delaying the test
PAUSE_BETWEEN_OET_TASK_LIST_CHECKS_IN_SECS = 5

LOGGER = logging.getLogger(__name__)

helm_release = environ.get("HELM_RELEASE", "test")
rest_cli_uri = f"http://oet-rest-{helm_release}:5000/api/v1.0/procedures"
REST_CLIENT = RestClientUI(rest_cli_uri)


class Subarray:

    resource = None

    def __init__(self, device):
        self.resource = resource(device)

    def get_obsstate(self):
        return self.resource.get('obsState')

    def get_state(self):
        return self.resource.get('State')

    def state_is(self, state):
        current_state = self.get_state()
        return current_state == state

    def obsstate_is(self, state):
        current_state = self.get_obsstate()
        return current_state == state


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


class Poller:
    proc = None
    device = None
    exit_q = None
    results = []

    def __init__(self, device):
        self.device = device

    def start_polling(self):
        manager = Manager()
        self.exit_q = Queue()
        self.results = manager.list()
        self.proc = Process(target=self.track_obsstates,
                            args=(self.device, self.results, self.exit_q))
        self.proc.start()

    def stop_polling(self):
        if self.proc is not None:
            self.exit_q.put(True)
            self.proc.join()

    def get_results(self):
        return self.results

    def track_obsstates(self, device, recorded_states, exit_q):
        LOGGER.info("STATE MONITORING: Started Tracking")
        while exit_q.empty():
            current_state = device.get_obsstate()
            if len(recorded_states) == 0 or current_state != recorded_states[-1]:
                LOGGER.info(
                    "STATE MONITORING: State has changed to %s", current_state)
                recorded_states.append(current_state)


class Task:
    @staticmethod
    def get_task_status(task, resp):
        """Extract a status for a task from the list
        If it isn't on the list return None so we can trap
        if we need to

        Args:
            task (str): Task ID being hunted for
            resp (str): The response message to be parsed

        Returns:
            str: The current OET status of the task or
            None if task is not present in resp
        """
        rest_responses = ScriptExecutor.parse_rest_response(resp)
        result_for_task = [x['state'] for x in rest_responses if x['id'] == task]
        if len(result_for_task) == 0:
            return None
        task_status = result_for_task[0]
        LOGGER.debug("Task Status is : %s", task_status)
        return task_status

    @staticmethod
    def task_has_status(task, expected_status, resp):
        """Confirm the task has the expected status by
        querying the OET client

        Args:
            task (str): OET ID for the task (script)
            expected_status (str): Expected script state
            resp (str): Response from OET REST CLI list

        Returns:
            bool: True if task is in expected_status
        """
        return Task.get_task_status(task, resp) == expected_status


class ScriptExecutor:
    @staticmethod
    def parse_rest_response_line(line):
        """Split a line from the REST API lines
        into columns

        Args:
            line (string): A line from OET REST CLI response

        Returns:
            rest_response_object: A dicts containing
            information on a script.
        """
        elements = line.split()
        rest_response_object = {
            'id': elements[0],
            'script': elements[1],
            'creation_time': str(elements[2] + ' ' + elements[3]),
            'state': elements[4]}
        return rest_response_object

    @staticmethod
    def parse_rest_response(resp):
        """Split the response from the REST API lines
        into columns

        Args:
            resp (string): Response from OET REST CLI

        Returns:
            [rest_response_object]: List of dicts containing
            information on each script.
        """
        rest_responses = []
        lines = resp.splitlines()
        del lines[0:2]
        for line in lines:
            rest_response_object = ScriptExecutor.parse_rest_response_line(line)
            rest_responses.append(rest_response_object)
        return rest_responses

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
            [rest_response_object]: List of dicts containing
            information on each script.
        """
        for line in resp:
            # Only get line with script details (ignore header lines)
            if 'RUNNING' in line:
                return [ScriptExecutor.parse_rest_response_line(line)]
        return []

    def confirm_script_status_and_return_id(self, resp, expected_status='CREATED'):
        """
        Confirm that the script is in a given state and return the ID

        Args:
            resp (str): Response from OET REST CLI list
            expected_status (str): Expected script state

        Returns:
            str: Task ID
        """
        if expected_status is 'RUNNING':
            details = ScriptExecutor.parse_rest_start_response(resp)
        else:
            details = ScriptExecutor.parse_rest_response(resp)
        assert_that(
            len(details), "Expected details for 1 script, instead got "
                          "details for {} scripts".format(len(details))).is_equal_to(1)
        resp_state = details[0].get('state')
        assert_that(
            resp_state,
            "The script status did not match the expected state"
        ).is_equal_to(expected_status)
        script_id = details[0].get('id')
        return script_id

    def execute_script(self, script, scheduling_block):
        resp = REST_CLIENT.create(script, subarray_id=1)
        # confirm that creating the task worked and we have a valid ID
        oet_create_task_id = self.confirm_script_status_and_return_id(resp, 'CREATED')
        # we  can now start the observing task passing in the scheduling block as a parameter
        resp = REST_CLIENT.start(scheduling_block, listen=False)
        # confirm that it didn't fail on starting
        oet_start_task_id = self.confirm_script_status_and_return_id(resp, 'RUNNING')

        # If task IDs do not match, wrong script was started
        if oet_create_task_id != oet_start_task_id:
            LOGGER.info("Script IDs did not match, created script with ID %s but started script with ID %s",
                        oet_create_task_id, oet_start_task_id)
            return False

        timeout = DEFAUT_LOOPS_DEFORE_TIMEOUT  # arbitrary number
        while timeout != 0:
            resp = REST_CLIENT.list()
            if not Task.task_has_status(oet_start_task_id, 'RUNNING', resp):
                LOGGER.info(
                    "PROCESS: Task has run to completion - no longer present on task list")
                return True
            time.sleep(PAUSE_BETWEEN_OET_TASK_LIST_CHECKS_IN_SECS)
            timeout -= 1
        # if we get here we timed out so need to fail the test
        return False
