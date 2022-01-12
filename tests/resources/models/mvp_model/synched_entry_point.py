from abc import abstractmethod
from contextlib import contextmanager
from typing import List

from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from . import waiting


class SynchedEntryPoint(EntryPoint):
    """A partially implemented entry point that performs predetermined waits to
    perform synchronized actions
    """

    builder = None

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def set_telescope_to_running(self):
        pass

    def set_wating_for_start_up(self) -> waiting.MessageBoardBuilder:
        return waiting.set_wating_for_start_up(self.builder)

    def set_waiting_for_assign_resources(
        self,
        sub_array_id: int,
    ) -> waiting.MessageBoardBuilder:
        return waiting.set_waiting_for_assign_resources(sub_array_id, self.builder)

    def set_waiting_for_release_resources(
        self,
        sub_array_id: int,
    ) -> waiting.MessageBoardBuilder:
        return waiting.set_waiting_for_release_resources(sub_array_id, self.builder)

    def set_wating_for_shut_down(
        self,
    ) -> waiting.MessageBoardBuilder:
        return waiting.set_wating_for_shut_down(self.builder)

    def set_waiting_for_configure(
        self, sub_array_id: int, receptors: List[int]
    ) -> waiting.MessageBoardBuilder:
        return waiting.set_waiting_for_configure_scan(
            sub_array_id, receptors, self.builder
        )

    def set_waiting_until_configuring(
        self, sub_array_id: int, receptors: List[int]
    ) -> waiting.MessageBoardBuilder:
        return waiting.set_waiting_until_configuring(
            sub_array_id, receptors, self.builder
        )

    def set_waiting_until_scanning(
        self, sub_array_id: int, receptors: List[int]
    ) -> waiting.MessageBoardBuilder:
        return waiting.set_waiting_until_scanning(sub_array_id, receptors, self.builder)

    def set_waiting_for_clear_configure(
        self, sub_array_id: int, receptors: List[int]
    ) -> waiting.MessageBoardBuilder:
        return waiting.set_waiting_for_releasing_a_configuration(
            sub_array_id, receptors, self.builder
        )

    def set_waiting_for_obsreset(
        self, sub_array_id: int, receptors: List[int]
    ) -> waiting.MessageBoardBuilder:
        return waiting.set_waiting_for_obsreset(sub_array_id, receptors, self.builder)

    def set_waiting_until_resourcing(
        self,
        sub_array_id: int,
    ) -> waiting.MessageBoardBuilder:
        return waiting.set_waiting_until_resourcing(sub_array_id, self.builder)

    def set_wating_for_scan_completion(
        self, sub_array_id: int, receptors: List[int]
    ) -> waiting.MessageBoardBuilder:
        return waiting.set_waiting_for_scanning_to_complete(
            sub_array_id, receptors, self.builder
        )
