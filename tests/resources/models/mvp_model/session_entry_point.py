"""Entrypoint to use for session wide commands."""
import logging
from typing import Callable, List, Union
from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from .waiting import MessageBoardBuilder

logger = logging.getLogger(__name__)


# TODO implement telescope on of commands for used in a session wide context


def get_session_entry_point() -> Callable[[], EntryPoint]:
    """Return an instance of session point
    :return: [description]
    :rtype: Callable[[], EntryPoint]
    """
    return SessionEntryPointLow


class SessionEntryPointLow(EntryPoint):
    """[summary]

    :param EntryPoint: [description]
    :type EntryPoint: [type]
    """

    def set_waiting_for_offline_components_to_become_online(
        self,
    ) -> Union[MessageBoardBuilder, None]:
        """[summary]

        :return: [description]
        :rtype: Union[MessageBoardBuilder, None]
        """
        return None

        # disable as mccs are flaky
        # if not (brd := super().set_waiting_for_offline_components_to_become_online()):
        #    brd = get_message_board_builder()
        # logging.info("setting up waiting for going online in Low")
        # chart = cast(DevicesChart, get_mvp_release().sub_charts["ska-low-mccs"])
        # for device in chart.devices.names:
        #    brd.set_waiting_on(device).for_attribute("state").to_change()
        # return brd

    def set_offline_components_to_online(self):
        """[summary]"""
        pass
        # logging.info("command mccs components to go into online")
        # chart = cast(DevicesChart, get_mvp_release().sub_charts["ska-low-mccs"])
        # try:
        #    chart.devices.write_attributes("adminmode", 0)
        # except ConcurrentTaskExecutionError as error:
        #    logger.exception(error)
        #    logger.warning("Will attempt to write attributes again after failure...")
        #    chart.devices.write_attributes("adminmode", 0, in_series=True)

    def set_telescope_to_running(self):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def set_telescope_to_standby(self):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def tear_down_subarray(self, sub_array_id: int):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def compose_subarray(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        composition,
        sb_id: str,
    ):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def clear_configuration(self, sub_array_id: int):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def configure_subarray(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        configuration,
        sb_id: str,
        duration: float,
    ):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def scan(self, sub_array_id: int):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def set_wating_for_scan_completion(self, sub_array_id: int, receptors: List[int]):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def set_wating_for_start_up(self):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def set_waiting_for_assign_resources(self, sub_array_id: int):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def set_waiting_for_configure(self, sub_array_id: int, receptors: List[int]):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def set_waiting_until_configuring(self, sub_array_id: int, receptors: List[int]):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def set_waiting_until_scanning(self, sub_array_id: int, receptors: List[int]):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def set_waiting_until_resourcing(self, sub_array_id: int):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def set_waiting_for_clear_configure(self, sub_array_id: int, receptors: List[int]):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def set_waiting_for_obsreset(self, sub_array_id: int, receptors: List[int]):
        """[summary]

        :param sub_array_id: [description]
        :param receptors: [description]

        :return: [description]
        """

    def set_waiting_for_release_resources(self, sub_array_id: int):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def set_wating_for_shut_down(
        self,
    ):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def abort_subarray(self, sub_array_id: int):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )

    def reset_subarray(self, sub_array_id: int):
        raise NotImplementedError(
            "Session entry point does not implement session wide behavior,"
            " please set DISABLE_MAINTAIN_ON=True"
        )
