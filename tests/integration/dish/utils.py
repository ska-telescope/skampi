import queue
from typing import Any

import tango
from tango import CmdArgType


def retrieve_attr_value(dev_proxy, attr_name):
    """Get the attribute reading from device"""
    current_val = dev_proxy.read_attribute(attr_name)
    if current_val.type == CmdArgType.DevEnum:
        current_val = getattr(dev_proxy, attr_name).name
    elif current_val.type == CmdArgType.DevState:
        current_val = str(current_val.value)
    else:
        current_val = current_val.value
    return current_val


class EventStore:
    """Store events with useful functionality"""

    def __init__(self) -> None:
        self._queue = queue.Queue()

    def push_event(self, event: tango.EventData):
        """Store the event

        :param event: Tango event
        :type event: tango.EventData
        """
        self._queue.put(event)

    def wait_for_value(  # pylint:disable=inconsistent-return-statements
        self, value: Any, timeout: int = 3
    ):
        """Wait for a value to arrive

        Wait `timeout` seconds for each fetch.

        :param value: The value to check for
        :type value: Any
        :param timeout: the get timeout, defaults to 3
        :type timeout: int, optional
        :raises RuntimeError: If None are found
        :return: True if found
        :rtype: bool
        """
        try:
            while True:
                event = self._queue.get(timeout=timeout)
                if not event.attr_value:
                    continue
                if event.attr_value.value != value:
                    continue
                if event.attr_value.value == value:
                    return True
        except queue.Empty as err:
            raise RuntimeError(
                f"Never got an event with value [{value}]"
            ) from err

    # pylint:disable=inconsistent-return-statements
    def wait_for_command_result(
        self, command_id: str, command_result: Any, timeout: int = 5
    ):
        """Wait for a long running command result

        Wait `timeout` seconds for each fetch.

        :param command_id: The long running command ID
        :type command_id: str
        :param timeout: the get timeout, defaults to 3
        :type timeout: int, optional
        :raises RuntimeError: If none are found
        :return: The result of the long running command
        :rtype: str
        """
        try:
            while True:
                event = self._queue.get(timeout=timeout)
                if not event.attr_value:
                    continue
                if not isinstance(event.attr_value.value, tuple):
                    continue
                if len(event.attr_value.value) != 2:
                    continue
                (lrc_id, lrc_result) = event.attr_value.value
                if command_id == lrc_id and command_result == lrc_result:
                    return True
        except queue.Empty as err:
            raise RuntimeError(
                f"Never got an LRC result from command [{command_id}]"
            ) from err

    def clear_queue(self):
        while not self._queue.empty():
            self._queue.get()

    #  pylint: disable=unused-argument
    def get_queue_events(self, timeout: int = 3):
        items = []
        try:
            while True:
                items.append(self._queue.get(timeout=timeout))
        except queue.Empty:
            return items

    def get_queue_values(self, timeout: int = 3):
        items = []
        try:
            while True:
                event = self._queue.get(timeout=timeout)
                items.append((event.attr_value.name, event.attr_value.value))
        except queue.Empty:
            return items
