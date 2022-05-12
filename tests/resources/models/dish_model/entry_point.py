"""Domain logic for the Dish."""
import logging
from typing import Dict, Literal, Union, List
import os


from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_fixtures.context_management import StackableContext
from ska_ser_skallop.mvp_control.event_waiting.wait import wait_for

from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    NoOpStep,
    MessageBoardBuilder,
)
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.event_handling.builders import get_message_board_builder

from .dish_pointing import Pointing, SourcePosition, start_as_cm, stop


logger = logging.getLogger(__name__)


class LogEnabled:
    """class that allows for logging if set by env var"""

    def __init__(self) -> None:
        self._live_logging = bool(os.getenv("DEBUG"))
        self._tel = names.TEL()

    def _log(self, mssage: str):
        if self._live_logging:
            logger.info(mssage)


class DishAssignStep(base.AssignResourcesStep, LogEnabled):
    """Implementation of Assign Resources Step for SDP."""

    dish_names: list[str] = [1, 2, 3, 4]

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()

    def do(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        composition: types.Composition,  # pylint: disable=
        sb_id: str,
    ):
        """Domain logic for assigning resources to a subarray in sdp.

        This implements the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration paramaters
        :param sb_id: a generic id to identify a sb to assign resources
        """
        # currently ignore composition as all types will be standard
        successfully_commanded_dishes: list[con_config.AbstractDeviceProxy] = []
        dish_names = self._tel.skamid.dishes(dish_ids).list
        for dish_name in dish_names:
            dish = con_config.get_device_proxy(dish_name, fast_load=True)
            self._log(f"setting {dish} to StandbyFPMode")
            dish.command_inout("SetStandbyFPMode")
            successfully_commanded_dishes.append(dish)

    def undo(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in sdp.

        This implments the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        successfully_commanded_dishes: list[con_config.AbstractDeviceProxy] = []
        try:
            for dish_name in self.dish_names:
                dish = con_config.get_device_proxy(dish_name, fast_load=True)
                dish.command_inout("SetStandbyLPMode")
                successfully_commanded_dishes.append(dish)
        except Exception as exception:
            self._log(
                f"Exception in commanding {dish_name} will revert commands on other dishes"
            )
            for successfully_commanded_dish in successfully_commanded_dishes:
                successfully_commanded_dish.command_inout("SetStandbyLPMode")
            raise exception

    def set_wait_for_do(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        brd = get_message_board_builder()
        for dish in self.dish_names:
            brd.set_waiting_on(dish).for_attribute("dishmode").to_become_equal_to(
                "STANDBY-FP", ignore_first=False
            )
        return brd

    def set_wait_for_doing(self, sub_array_id: int) -> MessageBoardBuilder:
        """Not implemented."""
        raise NotImplementedError()

    def set_wait_for_undo(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        brd = get_message_board_builder()
        for dish in self.dish_names:
            brd.set_waiting_on(dish).for_attribute("dishmode").to_become_equal_to(
                "STANDBY-FP", ignore_first=False
            )
        return brd


BandType = Literal["Band1", "Band2", "Band3", "Band4", "Band5a", "Band5b"]
BandConfigureCommand = Literal[
    "ConfigureBand1",
    "ConfigureBand2",
    "ConfigureBand3",
    "ConfigureBand4",
    "ConfigureBand5a",
    "ConfigureBand5b",
]


class SetBandStep(LogEnabled):
    """A 'sub' step specifically to a dish to change or setup a band on a nr of dishes."""

    band_configure_mapping: Dict[BandType, BandConfigureCommand] = {
        "Band1": "ConfigureBand1",
        "Band2": "ConfigureBand2",
        "Band3": "ConfigureBand3",
        "Band4": "ConfigureBand4",
        "Band5a": "ConfigureBand5a",
        "Band5b": "ConfigureBand5b",
    }

    def do(self, band: BandType, dish_ids: list[str]):
        """_summary_

        :param band: _description_
        :param dish_ids: _description_
        """
        successfully_commanded_dishes: list[con_config.AbstractDeviceProxy] = []
        try:
            for dish_name in self._tel.skamid.dishes(dish_ids):
                dish = con_config.get_device_proxy(dish_name)
                command = self.band_configure_mapping[band]
                self._log("Commanding {dish_name} with {command}")
                dish.command_inout(command, " ")
        except Exception as exception:
            self._log(
                f"Exception in commanding {dish_name} will revert commands on other dishes"
            )
            for successfully_commanded_dish in successfully_commanded_dishes:
                successfully_commanded_dish.command_inout("SetStandbyLPMode")
            raise exception

    def set_wait_for_do(
        self, band: BandType, dish_ids: list[str]
    ) -> Union[MessageBoardBuilder, None]:
        """Get specifications of what to wait for in order for configure band to be complete.


        :return: _description_
        :rtype: Union[MessageBoardBuilder, None]
        """
        brd = get_message_board_builder()
        for dish_name in self._tel.skamid.dishes(dish_ids):
            brd.set_waiting_on(dish_name).for_attribute(
                "configuredBand"
            ).to_become_equal_to(band)
        return brd

    def undo(self):
        """_summary_

        :return: _description_
        :rtype: _type_
        :yield: _description_
        :rtype: _type_
        """
        pass

    def set_wait_for_undo(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic for what needs to be waited for switching the Dish off."""
        pass


class SetReadyStep(LogEnabled):
    """A 'sub' step specifically to ensure dish is ready for pointing.

    (must be preceded by a SetBandStep step)
    """

    def do(self, dish_ids: list[str]):
        """_summary_

        :param band: _description_
        :param dish_ids: _description_
        """
        successfully_commanded_dishes: list[con_config.AbstractDeviceProxy] = []
        try:
            for dish_name in self._tel.skamid.dishes(dish_ids):
                dish = con_config.get_device_proxy(dish_name)
                self._log("Commanding {dish_name} with SetOperateMode")
                dish.command_inout("SetOperateMode")
        except Exception as exception:
            self._log(
                f"Exception in commanding {dish_name} will revert commands on other dishes"
            )
            for successfully_commanded_dish in successfully_commanded_dishes:
                successfully_commanded_dish.command_inout("SetStandbyLPMode")
            raise exception

    def set_wait_for_do(self, dish_ids: list[int]) -> Union[MessageBoardBuilder, None]:
        """Get specifications of what to wait for in order for configure band to be complete.


        :return: _description_
        :rtype: Union[MessageBoardBuilder, None]
        """
        brd = get_message_board_builder()
        for dish_name in self._tel.skamid.dishes(dish_ids):
            brd.set_waiting_on(dish_name).for_attribute(
                "pointingstate"
            ).to_become_equal_to("READY", ignore_first=False)
        return brd

    def undo(self):
        """_summary_

        :return: _description_
        :rtype: _type_
        :yield: _description_
        :rtype: _type_
        """
        pass

    def set_wait_for_undo(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic for what needs to be waited for switching the Dish off."""
        pass


class PointingStep:
    """ "A 'sub' step of configuration that realizes the pointing behavior on the dish."""

    def __init__(self, context: StackableContext) -> None:
        self._pointings: list[Pointing] = []
        self._context = context
        self._tel = names.TEL()
        self._dish_ids = []

    def do(self, dish_ids: list[str], source: SourcePosition, polling=0.05):
        """_summary_

        :param dish_ids: _description_
        :param source: _description_
        :param polling: _description_, defaults to 0.05
        """
        self._pointings = self._context.push_context_onto_test(
            start_as_cm(dish_ids, source, polling)
        )

    def set_wait_for_do(self, dish_ids: list[int]) -> Union[MessageBoardBuilder, None]:
        """_summary_

        :raises NotImplementedError: _description_
        :return: _description_
        :rtype: Union[MessageBoardBuilder, None]
        """
        brd = get_message_board_builder()
        # TODO currently there is a bug in that the pointing state
        # should end up as Track but we use READY as our indicator
        # until bug is fixed
        for dish_name in self._tel.skamid.dishes(dish_ids):
            brd.set_waiting_on(dish_name).for_attribute(
                "pointingstate"
            ).to_become_equal_to("READY")
        return brd

    def undo(self):
        stop(self._pointings)

    def set_pass(self, dish_ids: list[int]) -> Union[MessageBoardBuilder, None]:
        """_summary_

        :param dish_ids: _description_
        :type dish_ids: list[int]
        :return: _description_
        :rtype: Union[MessageBoardBuilder, None]
        """ """_summary_

    :raises NotImplementedError: _description_
    :return: _description_
    :rtype: Union[MessageBoardBuilder, None]
    """

    pass


class DishConfigureStep(base.ConfigureStep, LogEnabled):
    """Implementation of Configure Scan Step for Dish."""

    def __init__(
        self,
        context: StackableContext,
        set_band_step: SetBandStep,
        set_ready_step: SetReadyStep,
        pointing_step: PointingStep,
    ) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()
        self._context = context
        self.set_band_step = set_band_step
        self.set_ready_step = set_ready_step
        self.pointing_step = pointing_step
        self.exec_settings = None

    def do(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        configuration: types.ScanConfiguration,
        sb_id: str,
        duration: float,
    ):
        """Domain logic for configuring a scan on subarray in Dish.

        This implements the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration paramaters
        :param sb_id: a generic ide to identify a sb to assign resources
        """
        # first we configure the band
        band: BandType = "Band2"
        configure_band_to_finish = self.set_band_step.set_wait_for_do(band, dish_ids)
        with wait_for(configure_band_to_finish, timeout=10):
            self.set_band_step.do(band, dish_ids)
        # then we set it to operational
        set_ready_to_finish = self.set_ready_step.set_wait_for_do(dish_ids)
        with wait_for(set_ready_to_finish, timeout=10):
            self.set_ready_step.do()
        set_pointing_to_start = self.pointing_step.set_wait_for_do(dish_ids)
        with wait_for(set_pointing_to_start, timeout=10):
            self.pointing_step.do()

    def undo(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in Dish.

        This implments the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """

    def set_wait_for_do(
        self, sub_array_id: int, receptors: List[int]
    ) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for configuring a scan is done.

        :param sub_array_id: The index id of the subarray to control
        """
        return None

    def set_wait_for_doing(
        self, sub_array_id: int, receptors: List[int]
    ) -> MessageBoardBuilder:
        """Not implemented."""
        raise NotImplementedError()

    def set_wait_for_undo(
        self, sub_array_id: int, receptors: List[int]
    ) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray clear scan config is done.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        """
        return None

    """Type of sybarray step that does not do anything."""

    def do(self, sub_array_id: int):
        pass

    def set_wait_for_do(self, sub_array_id: int) -> Union[MessageBoardBuilder, None]:
        pass

    def set_wait_for_doing(self, sub_array_id: int) -> Union[MessageBoardBuilder, None]:
        pass

    def undo(self, sub_array_id: int):
        pass

    def set_wait_for_undo(self, sub_array_id: int) -> Union[MessageBoardBuilder, None]:
        pass


class DishEntryPoint(CompositeEntryPoint):
    """Derived Entrypoint scoped to Dish element."""

    _dishes_assigned = [1, 2, 3, 4]

    def __init__(self) -> None:
        """Init Object"""
        super().__init__()
        self.set_online_step = NoOpStep()
        self.start_up_step = NoOpStep()
        self.assign_resources_step = DishAssignStep()
        self.configure_scan_step = DishConfigureStep()
        self.scan_step = NoOpStep()

    @property
    def dishes_assigned(self) -> list[int]:
        return self._dishes_assigned

    @dishes_assigned.setter
    def dishes_assigned(self, receptors: list[int]):
        self._dishes_assigned = receptors
        self.assign_resources_step.dish_names = receptors
