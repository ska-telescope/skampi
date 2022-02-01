import logging
from typing import Callable, List, Union, cast

from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from ska_ser_skallop.mvp_control.describing.mvp_names import TEL
from ska_ser_skallop.utils.piping import ConcurrentTaskExecutionError
from typing import cast

from ska_ser_skallop.mvp_control.infra_mon.configuration import (
    get_mvp_release,
    DevicesChart,
)

logger = logging.getLogger(__name__)

from .waiting import MessageBoardBuilder, get_message_board_builder

# TODO implement telescope on of commands for used in a session wide context


def get_session_entry_point() -> Callable[[], EntryPoint]:
    tel = TEL()
    if tel.skalow:
        return SessionEntryPointLow
    return EntryPoint


class SessionEntryPointLow(EntryPoint):
    def set_waiting_for_offline_components_to_become_online(
        self,
    ) -> Union[MessageBoardBuilder, None]:

        if not (brd := super().set_waiting_for_offline_components_to_become_online()):
            brd = get_message_board_builder()
        logging.info("setting up waiting for going online in Low")
        chart = cast(DevicesChart, get_mvp_release().sub_charts["ska-low-mccs"])
        for device in chart.devices.names:
            brd.set_waiting_on(device).for_attribute("state").to_change()
        return brd

    def set_offline_components_to_online(self):

        logging.info("command mccs components to go into online")
        chart = cast(DevicesChart, get_mvp_release().sub_charts["ska-low-mccs"])
        try:
            chart.devices.write_attributes("adminmode", 0)
        except ConcurrentTaskExecutionError as error:
            logger.exception(error)
            logger.warning("Will attempt to write attributes again after failure...")
            chart.devices.write_attributes("adminmode", 0)
