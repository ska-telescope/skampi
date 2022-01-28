import logging
from typing import Callable, List, Union, cast

from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from ska_ser_skallop.mvp_control.describing.mvp_names import TEL
from ska_ser_skallop.mvp_control.infra_mon import configuration
from typing import cast

from ska_ser_skallop.mvp_control.infra_mon.configuration import (
    get_mvp_release,
    DevicesChart,
)


from .waiting import MessageBoardBuilder, get_message_board_builder

# TODO implement telescope on of commands for used in a session wide context


def get_session_entry_point() -> Callable[[], EntryPoint]:
    tel = TEL()
    if tel.skalow:
        return SessionEntryPointLow
    else:
        return EntryPoint


class SessionEntryPointLow(EntryPoint):
    def __init__(self) -> None:
        super().__init__()

    def _get_mccs_devices(self) -> List[str]:
        release = configuration.get_mvp_release()
        mccs_chart = cast(
            configuration.DevicesChart, release.sub_charts["ska-low-mccs"]
        )
        device_allocation = mccs_chart.device_allocation
        return [
            device for device, allocation in device_allocation.items() if allocation.pod
        ]

    def set_waiting_for_offline_components_to_become_online(
        self,
    ) -> Union[MessageBoardBuilder, None]:

        if not (brd := super().set_waiting_for_offline_components_to_become_online()):
            brd = get_message_board_builder()
        logging.info("setting up waiting for going online in Low")
        chart = cast(DevicesChart, get_mvp_release().sub_charts["ska-low-mccs"])
        for device in chart.devices.names:
            brd.set_waiting_on(device).for_attribute("state").to_become_equal_to(
                ["OFF", "ON"]
            )

    def set_offline_components_to_online(self):

        logging.info("setting up waiting for going online in Low")
        chart = cast(DevicesChart, get_mvp_release().sub_charts["ska-low-mccs"])
        chart.devices.write_attributes("adminmode", 0)
