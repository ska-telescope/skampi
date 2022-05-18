import logging
import time
from os import environ

from ska_oso_oet.procedure.application.restclient import RestClientUI

LOGGER = logging.getLogger(__name__)

helm_release = environ.get("HELM_RELEASE", "test")
rest_cli_uri = f"http://ska-oso-oet-rest-{helm_release}:5000/api/v1.0/procedures"
REST_CLIENT = RestClientUI(rest_cli_uri)


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
            creation_time=str(elements[2] + " " + elements[3]),
            state=elements[4],
        )
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
        LOGGER.info(f"oet rest cli response {lines}")
        # Remove the headers
        del lines[0:2]
        # Remove the 'For more details..' line
        del lines[-1]
        for line in lines:
            task = ScriptExecutor.parse_rest_response_line(line)
            task_list.append(task)
        return task_list

    @staticmethod
    def parse_rest_start_response(resp):
        """Split the response from the REST API start
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
            if "RUNNING" in line or "READY" in line:
                return ScriptExecutor.parse_rest_response_line(line)
        return None

    @staticmethod
    def wait_for_script_state(task_id, state, timeout):
        """
        Wait until the script with the given ID is in the given state

        Args:
            task_id (str): ID of the script on the task list
            state (str): The desired OET state for the script (eg 'READY')
            timeout (int): timeout (~seconds) how long to wait
            for script to complete

        Returns:
            task: Task representing the script when in the desired state.
            None if timeout occurs before script in desired state.
        """
        t = timeout
        while t != 0:
            task = ScriptExecutor().get_script_by_id(task_id)
            if task.state_is(state):
                LOGGER.info(f"Script state changed to {state}")
                return task
            time.sleep(1)
            t -= 1

        LOGGER.info(
            "Timeout occurred (> %d seconds) when waiting for script "
            "to change state to %s. Stopping script.",
            timeout, state
        )
        ScriptExecutor().stop_script()
        task = ScriptExecutor().get_script_by_id(task_id)
        LOGGER.info("Script state: %s", task.state)
        return task.state

    def create_script(self, script) -> Task:
        resp = REST_CLIENT.create(script, subarray_id=1)
        tasks = ScriptExecutor.parse_rest_response(resp)
        return tasks[0]

    def start_script(self, task_id, *script_args) -> Task:
        resp = REST_CLIENT.start(task_id, *script_args, listen=False)
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

    def execute_script(self, script, *script_run_args, timeout=30):
        """
        Execute the given script using OET REST client.

        Args:
            script (str): Script file to execute
            script_run_args: Arguments to pass to the script when
            the script execution is started
            timeout: Timeout (~seconds) for how long to wait for script
            to complete

        Returns:
            Task: The Task representing the script after completion.
            None if something goes wrong.
        """
        LOGGER.info("Running script %s", script)

        # create script
        created_task = self.create_script(script)

        # confirm that creating the task worked and we have a valid ID
        if not self.wait_for_script_state(created_task.task_id, 'READY', timeout):
            LOGGER.info(
                "Script did not reach READY state"
            )
            return None

        # start execution of created script
        started_task = self.start_script(created_task.task_id, *script_run_args)

        return ScriptExecutor.wait_for_script_state(
            started_task.task_id, "COMPLETE", timeout
        )
