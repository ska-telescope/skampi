import logging
import time
from os import environ
from typing import List, Optional

from ska_db_oda.unit_of_work.restunitofwork import RESTUnitOfWork
from ska_oso_oet_client.activityclient import ActivityAdapter
from ska_oso_oet_client.procedureclient import ProcedureAdapter, ProcedureSummary

LOGGER = logging.getLogger(__name__)

kube_namespace = environ.get("KUBE_NAMESPACE", "test")
kube_host = environ.get("KUBE_HOST")
rest_cli_uri = f"http://{kube_host}/{kube_namespace}/ska-oso-oet/api/v1.0"
REST_ADAPTER = ProcedureAdapter(rest_cli_uri + "/procedures")
ACTIVITY_ADAPTER = ActivityAdapter(rest_cli_uri + "/activities")


def add_sb_to_oda(test_sbd):
    oda = RESTUnitOfWork()

    with oda:
        try:
            existing_sbd = oda.sbds.get(test_sbd.sbd_id)
            test_sbd.metadata.version = existing_sbd.metadata.version
            # Only save the SB if there have been changes to it
            if not existing_sbd == test_sbd:
                oda.sbds.add(test_sbd)
                oda.commit()
        except KeyError:
            # sbd_id doesn't exist in ODA so no need to worry about versions
            oda.sbds.add(test_sbd)
            oda.commit()


class ScriptExecutor:
    @staticmethod
    def init_script(script_uri: str, create_kwargs, *args, **kwargs) -> ProcedureSummary:
        if not kwargs:
            kwargs = dict()
        if "subarray_id" not in kwargs:
            kwargs["subarray_id"] = 1
        init_args = dict(args=args, kwargs=kwargs)
        return REST_ADAPTER.create(script_uri=script_uri, init_args=init_args, **create_kwargs)

    @staticmethod
    def start_script(pid: int, *args, **kwargs) -> ProcedureSummary:
        run_args = dict(args=args, kwargs=kwargs)
        return REST_ADAPTER.start(pid=pid, run_args=run_args)

    @staticmethod
    def stop_script(pid: int, run_abort: bool = False) -> None:
        REST_ADAPTER.stop(pid, run_abort=run_abort)

    @staticmethod
    def list_scripts() -> List[ProcedureSummary]:
        return REST_ADAPTER.list()

    @staticmethod
    def get_latest_script() -> Optional[ProcedureSummary]:
        procedures = ScriptExecutor.list_scripts()
        if procedures:
            return procedures[-1]
        return None

    @staticmethod
    def get_script_by_id(pid: int) -> Optional[ProcedureSummary]:
        procedures_by_id = REST_ADAPTER.list(pid)
        if procedures_by_id:
            return procedures_by_id[0]
        return None

    @staticmethod
    def wait_for_script_state(pid: int, state: str, timeout: int) -> str:
        """
        Wait until the script with the given ID is in the given state


        :param pid: ID of the script in the OET
        :type pid: int
        :param state: The desired OET state for the script (eg 'READY')
        :type state: str
        :param timeout: timeout (~seconds) how long to wait
                for script to complete
        :type timeout: int

        :return: Either the desired state, STOPPED if the timeout was
                reached or FAILED if the script failed
        :rtype: str
        """
        t = timeout
        while t > 0:
            procedure = ScriptExecutor.get_script_by_id(pid)

            if procedure.state == "FAILED":
                stacktrace = procedure.history["stacktrace"]
                LOGGER.info(
                    f"Script {procedure.script['script_uri']} (PID={pid})"
                    " failed. Stacktrace follows:"
                )
                LOGGER.exception(stacktrace)
                return procedure.state

            if procedure.state == state:
                LOGGER.info(
                    f"Script {procedure.script['script_uri']} state changed to" f" {state}"
                )
                return procedure.state

            time.sleep(2)
            t -= 2

        LOGGER.info(
            f"Timeout occurred (> {timeout} seconds) when waiting for script "
            f"to change state to {state}. Stopping script."
        )
        ScriptExecutor.stop_script(pid)
        procedure = ScriptExecutor.get_script_by_id(pid)
        LOGGER.info(f"Script {procedure.script['script_uri']} state: {procedure.state}")
        return procedure.state

    @staticmethod
    def execute_script(script: str, *script_run_args, timeout=60, script_create_kwargs={}) -> str:
        """
        Execute the given script using OET REST client.

        :parma script: Script file to execute
        :type script: str
        :param script_run_args: Arguments to pass to the script when
                the script execution is started
        :param timeout: Timeout (~seconds) for how long to wait for script
                stages to complete
        :param script_create_kwargs: Any keyword arguments
                (e.g. git related args) to pass to
                OET rest server when creating the script

        :return: The OET state for the script
                after execution (eg 'COMPLETE')
                None if something goes wrong.
        :rtype: str
        """
        LOGGER.info(f"Running script {script}")

        procedure = ScriptExecutor.init_script(script, create_kwargs=script_create_kwargs)
        pid = procedure.uri.split("/")[-1]

        # confirm that creating the script worked and we have a valid ID
        state = ScriptExecutor.wait_for_script_state(pid, "READY", timeout)
        if state != "READY":
            LOGGER.info(f"Script {script} did not reach READY state")
            return state

        # start execution of created script
        ScriptExecutor.start_script(pid, *script_run_args)

        return ScriptExecutor.wait_for_script_state(pid, "COMPLETE", timeout)
