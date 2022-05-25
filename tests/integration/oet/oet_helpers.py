from concurrent.futures import ThreadPoolExecutor
from threading import Event
from contextlib import contextmanager
import logging
import time
from os import environ
from typing import List, Optional, Union

from ska_oso_oet.procedure.application.application import ProcedureSummary
from ska_oso_oet.procedure.application.restclient import RestAdapter
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.mvp_control.event_waiting.wait import wait, MessageBoardBase
from ska_ser_skallop.subscribing.exceptions import EventTimedOut
from ska_ser_skallop.mvp_fixtures.env_handling import ExecSettings

LOGGER = logging.getLogger(__name__)

kube_namespace = environ.get("KUBE_NAMESPACE", "test")
kube_host = environ.get("KUBE_HOST")
rest_cli_uri = f"http://{kube_host}/{kube_namespace}/api/v1.0/procedures"
REST_ADAPTER = RestAdapter(rest_cli_uri)


class ScriptExecutor:
    @staticmethod
    def init_script(script_uri: str, *args, **kwargs) -> ProcedureSummary:
        if not kwargs:
            kwargs = dict()
        if "subarray_id" not in kwargs:
            kwargs["subarray_id"] = 1
        init_args = dict(args=args, kwargs=kwargs)
        return REST_ADAPTER.create(script_uri=script_uri, init_args=init_args)

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

        Args:
            pid (str): ID of the script in the OET
            state (str): The desired OET state for the script (eg 'READY')
            timeout (int): timeout (~seconds) how long to wait
            for script to complete

        Returns:
            state (str): Either the desired state, STOPPED if the timeout was
                reached or FAILED if the script failed
        """
        t = timeout
        while t != 0:
            procedure = ScriptExecutor.get_script_by_id(pid)

            if procedure.state == "FAILED":
                stacktrace = procedure.history["stacktrace"]
                LOGGER.info(
                    f"Script {procedure.script['script_uri']} (PID={pid}) failed. Stacktrace follows:"
                )
                LOGGER.exception(stacktrace)
                return procedure.state

            if procedure.state == state:
                LOGGER.info(
                    f"Script {procedure.script['script_uri']} state changed to {state}"
                )
                return procedure.state

            time.sleep(5)
            t -= 5

        LOGGER.info(
            f"Timeout occurred (> {timeout} seconds) when waiting for script "
            f"to change state to {state}. Stopping script."
        )
        ScriptExecutor.stop_script(pid)
        procedure = ScriptExecutor.get_script_by_id(pid)
        LOGGER.info(f"Script {procedure.script.script_uri} state: {procedure.state}")
        return procedure.state

    @staticmethod
    def execute_script(script: str, *script_run_args, timeout=30) -> str:
        """
        Execute the given script using OET REST client.

        Args:
            script (str): Script file to execute
            script_run_args: Arguments to pass to the script when
            the script execution is started
            timeout: Timeout (~seconds) for how long to wait for script
            stages to complete

        Returns:
            state: The OET state for the script after execution (eg 'COMPLETE')
            None if something goes wrong.
        """
        LOGGER.info(f"Running script {script}")

        procedure = ScriptExecutor.init_script(script)
        pid = procedure.uri.split("/")[-1]

        # confirm that creating the script worked and we have a valid ID
        state = ScriptExecutor.wait_for_script_state(pid, "READY", timeout)
        if state != "READY":
            LOGGER.info(f"Script {script} did not reach READY state")
            return state

        # start execution of created script
        ScriptExecutor.start_script(pid, *script_run_args)

        return ScriptExecutor.wait_for_script_state(pid, "COMPLETE", timeout)


def concurrent_wait(
    board: MessageBoardBase,
    stop_signal: Event,
    polling: float,
    live_logging=False,
):
    """Waiting task that can be used in concurrent tasks allowing for a stop_signal to stop waiting.

    This function should be implemented in skallop.

    :param board: _description_

    :param stop_signal: _description_

    :param timeout: _description_

    :param live_logging: _description_, defaults to False
    :type live_logging: bool, optional
    """

    while stop_signal.is_set():
        try:
            item = next(board.get_items(polling))
        except EventTimedOut:
            # we treat timeout as a signal indicating no incoming message
            # events occurred within a given period but does not mean
            # we need to stop listening as that is determined by stop signal
            continue
        handler = item.handler
        if handler:
            handler.handle_event(item.event, item.subscription)
            message = handler.print_event(item.event, ignore_first=False)
            if live_logging:
                LOGGER.info(message)
    board.remove_all_subscriptions()


@contextmanager
def observe_while_running(
    context_monitoring: fxt_types.context_monitoring,
    settings: Union[None, ExecSettings] = None,
):
    """Handle messages from incoming events in a background thread whilst running the main thread.

    This mechanism does not block until all event handlers have been concluded but
    rather immediately stop subscriptions when the main thread has finished within
    the context.

    Note, if this function is proved useful it should rather be exported as a method
    of ContextMonitoring
    in skallop package.
    :param context_monitoring: the ContextMonitoring object (should be self in skallop)
    :param settings: settings related to the waiting whilst running the main thread
        , defaults to None
    """
    poll_period = 0.1
    settings = settings if settings else ExecSettings()
    with context_monitoring.context_monitoring():
        with ThreadPoolExecutor(max_workers=2) as pool:
            board = context_monitoring.builder.setup_board()
            stop_signal = Event()
            stop_signal.set()
            pool.submit(
                concurrent_wait,
                board,
                stop_signal,
                poll_period,
                settings.log_enabled,
            )
            yield
            # at the end of the task we end waiting by cancelling all subscriptions
            stop_signal.clear()
