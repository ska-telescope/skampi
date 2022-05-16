"""Domain logic for the Dish."""
import logging
from typing import Dict, Literal, Union, List, cast
import os


from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_fixtures.context_management import StackableContext
from ska_ser_skallop.mvp_control.event_waiting.wait import wait_for
from ska_ser_skallop.utils.singleton import Memo

from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    NoOpStep,
    MessageBoardBuilder,
    ScanStep,
)
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.event_handling.builders import (
    get_message_board_builder,
    clear_supscription_specs,
)

from .dish_pointing import Pointing, SourcePosition, start_as_cm, stop, start


logger = logging.getLogger(__name__)


class LogEnabled:
    """class that allows for logging if set by env var"""

    def __init__(self) -> None:
        self._live_logging = bool(os.getenv("DEBUG"))
        self._skamid = cast(names.Mid, names.TEL().skamid)
        assert self._skamid, "wrong telescope, this is Mid only"

    def _log(self, mssage: str):
        if self._live_logging:
            logger.info(mssage)


class DishAssignStep(base.AssignResourcesStep, LogEnabled):
    """Implementation of Assign Resources Step for SDP."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        self._skamid = cast(names.Mid, names.TEL().skamid)
        assert self._skamid, "wrong telescope, this is Mid only"

    @property
    def dishes_to_assign(self) -> list[int]:
        return Memo().get("dishes_to_assign")

    @dishes_to_assign.setter
    def dishes_to_assign(self, receptors: list[int]):
        Memo(dishes_to_assign=receptors)

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
        assert self.dishes_to_assign == dish_ids, (
            "The dishes intended to be assigned does not match with those"
            "being prepared to wait for as indicated by the `dishes_to_assign` property,"
            "did you remember to set them on the entrypoint beforehand?"
        )
        successfully_commanded_dishes: list[con_config.AbstractDeviceProxy] = []
        dish_names = self._skamid.dishes(self.dishes_to_assign).list
        dish_name = ""
        try:
            for dish_name in dish_names:
                dish = con_config.get_device_proxy(dish_name, fast_load=True)
                self._log(f"setting {dish_name} to StandbyFPMode")
                dish.command_inout("SetStandbyFPMode")
                successfully_commanded_dishes.append(dish)
        except Exception as exception:
            self._log(
                f"Exception in commanding {dish_name} will revert commands on other dishes"
            )
            for successfully_commanded_dish in successfully_commanded_dishes:
                successfully_commanded_dish.command_inout("SetStandbyLPMode")
            raise exception

    def undo(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in sdp.

        This implements the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        dish_names = self._skamid.dishes(self.dishes_to_assign).list
        for dish_name in dish_names:
            dish = con_config.get_device_proxy(dish_name, fast_load=True)
            self._log(f"setting {dish_name} to SetStandbyLPMode")
            dish.command_inout("SetStandbyLPMode")

    def set_wait_for_do(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        brd = get_message_board_builder()
        dish_names = self._skamid.dishes(self.dishes_to_assign).list
        for dish in dish_names:
            brd.set_waiting_on(dish).for_attribute("dishmode").to_become_equal_to(
                "STANDBY_FP", ignore_first=False
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
        dish_names = self._skamid.dishes(self.dishes_to_assign).list
        for dish in dish_names:
            brd.set_waiting_on(dish).for_attribute("dishmode").to_become_equal_to(
                "STANDBY_LP", ignore_first=False
            )
        return brd


BandType = Literal["B1", "B2", "B3", "B4", "B5a", "B5b"]
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
        "B1": "ConfigureBand1",
        "B2": "ConfigureBand2",
        "B3": "ConfigureBand3",
        "B4": "ConfigureBand4",
        "B5a": "ConfigureBand5a",
        "B5b": "ConfigureBand5b",
    }

    def do(self, band: BandType, dish_ids: list[int]):
        """_summary_

        :param band: _description_
        :param dish_ids: _description_
        """
        successfully_commanded_dishes: list[con_config.AbstractDeviceProxy] = []
        dish_name = ""
        try:
            for dish_name in self._skamid.dishes(dish_ids):
                dish = con_config.get_device_proxy(dish_name)
                command = self.band_configure_mapping[band]
                self._log(f"Commanding {dish_name} with {command}")
                dish.command_inout(command, " ")
        except Exception as exception:
            self._log(
                f"Exception in commanding {dish_name} will revert commands on other dishes"
            )
            for successfully_commanded_dish in successfully_commanded_dishes:
                successfully_commanded_dish.command_inout("SetStandbyLPMode")
            raise exception

    def set_wait_for_do(
        self, band: BandType, dish_ids: list[int]
    ) -> MessageBoardBuilder:
        """Get specifications of what to wait for in order for configure band to be complete.


        :return: _description_
        :rtype: Union[MessageBoardBuilder, None]
        """
        brd = get_message_board_builder()
        for dish_name in self._skamid.dishes(dish_ids):
            brd.set_waiting_on(dish_name).for_attribute(
                "configuredBand"
            ).to_become_equal_to(band, ignore_first=False)
        return brd

    def undo(self):
        """_summary_

        :return: _description_
        :rtype: _type_
        :yield: _description_
        :rtype: _type_
        """
        pass

    def set_wait_for_undo(self) -> MessageBoardBuilder:
        """Domain logic for what needs to be waited for switching the Dish off."""
        return get_message_board_builder()


class SetReadyStep(LogEnabled):
    """A 'sub' step specifically to ensure dish is ready for pointing.

    (must be preceded by a SetBandStep step)
    """

    @property
    def configured_dishes(self) -> list[int]:
        return Memo().get("configured_dishes")

    @configured_dishes.setter
    def configured_dishes(self, dish_ids: list[int]):
        Memo(configured_dishes=dish_ids)

    def do(self, dish_ids: list[int]):
        """_summary_

        :param band: _description_
        :param dish_ids: _description_
        """
        successfully_commanded_dishes: list[con_config.AbstractDeviceProxy] = []
        dish_name = ""
        try:
            for dish_name in self._skamid.dishes(dish_ids):
                dish = con_config.get_device_proxy(dish_name)
                self._log(f"Commanding {dish_name} with SetOperateMode")
                dish.command_inout("SetOperateMode")
        except Exception as exception:
            self._log(
                f"Exception in commanding {dish_name} will revert commands on other dishes"
            )
            for successfully_commanded_dish in successfully_commanded_dishes:
                successfully_commanded_dish.command_inout("SetStandbyFPMode")
            raise exception

    def set_wait_for_do(self, dish_ids: list[int]) -> MessageBoardBuilder:
        """Get specifications of what to wait for in order for configure band to be complete.


        :return: _description_
        :rtype: Union[MessageBoardBuilder, None]
        """
        brd = get_message_board_builder()
        for dish_name in self._skamid.dishes(dish_ids):
            brd.set_waiting_on(dish_name).for_attribute(
                "pointingstate"
            ).to_become_equal_to("READY", ignore_first=False)
        for dish_name in self._skamid.dishes(dish_ids):
            brd.set_waiting_on(dish_name).for_attribute("dishmode").to_become_equal_to(
                "OPERATE", ignore_first=False
            )
        return brd

    def undo(self):
        """_summary_

        :return: _description_
        :rtype: _type_
        :yield: _description_
        :rtype: _type_
        """
        for dish_name in self._skamid.dishes(self.configured_dishes):
            dish = con_config.get_device_proxy(dish_name)
            self._log(
                f"Reverting Operate state from {dish_name} by commanding it with SetStandbyFP"
            )
            dish.command_inout("SetStandbyFPMode")

    def set_wait_for_undo(self) -> MessageBoardBuilder:
        """Domain logic for what needs to be waited for switching the Dish off."""
        brd = get_message_board_builder()
        for dish_name in self._skamid.dishes(self.configured_dishes):
            brd.set_waiting_on(dish_name).for_attribute(
                "pointingstate"
            ).to_become_equal_to("NONE", ignore_first=False)
        for dish_name in self._skamid.dishes(self.configured_dishes):
            brd.set_waiting_on(dish_name).for_attribute("dishmode").to_become_equal_to(
                "STANDBY_FP", ignore_first=False
            )
        return brd


class PointingStep(LogEnabled):
    """ "A 'sub' step of configuration that realizes the pointing behavior on the dish."""

    def __init__(self, context: Union[StackableContext, None] = None) -> None:
        """Init object."""
        super().__init__()
        self._context = context
        self._dish_ids = []

    def set_stackable_context(self, context: StackableContext):
        self._context = context

    @property
    def configured_dishes(self) -> list[int]:
        return Memo().get("configured_dishes")

    @configured_dishes.setter
    def configured_dishes(self, dish_ids: list[int]):
        Memo(configured_dishes=dish_ids)

    @property
    def _pointings(self) -> list[Pointing]:
        return Memo().get("_pointings")

    @_pointings.setter
    def _pointings(self, pointings: list[Pointing]):
        Memo(_pointings=pointings)

    def do(self, dish_ids: list[int], source: SourcePosition, polling: float = 0.05):
        """_summary_

        :param dish_ids: _description_
        :param source: _description_
        :param polling: _description_, defaults to 0.05
        """
        self._log("starting pointing threads...")
        if self._context:
            self._pointings = self._context.push_context_onto_test(
                start_as_cm(dish_ids, source, polling)
            )
        else:
            self._pointings = start(dish_ids, source, polling)
        self.configured_dishes = dish_ids

    def set_wait_for_do(self, dish_ids: list[int]) -> MessageBoardBuilder:
        """_summary_

        :raises NotImplementedError: _description_
        :return: _description_
        :rtype: Union[MessageBoardBuilder, None]
        """
        brd = get_message_board_builder()
        # TODO currently there is a bug in that the pointing state
        # should end up as Track but we use READY as our indicator
        # until bug is fixed
        for dish_name in self._skamid.dishes(dish_ids):
            brd.set_waiting_on(dish_name).for_attribute(
                "pointingstate"
            ).to_become_equal_to("TRACK")
        return brd

    def undo(self):
        self._log("stopping pointing threads...")
        stop(self._pointings)

    def set_wait_for_undo(self, dish_ids: list[int]) -> MessageBoardBuilder:
        """_summary_

        :param dish_ids: _description_
        :type dish_ids: list[int]
        :return: _description_
        :rtype: Union[MessageBoardBuilder, None]
        """
        brd = get_message_board_builder()
        for dish_name in self._skamid.dishes(dish_ids):
            brd.set_waiting_on(dish_name).for_attribute(
                "pointingstate"
            ).to_become_equal_to("READY")
        return brd


class DishConfigureStep(base.ConfigureStep, LogEnabled):
    """Implementation of Configure Scan Step for Dish."""

    def __init__(
        self,
        set_band_step: SetBandStep,
        set_ready_step: SetReadyStep,
        pointing_step: PointingStep,
    ) -> None:
        """Init object."""
        super().__init__()
        self._skamid = names.TEL().skamid
        assert self._skamid, "wrong telescope, this is Mid only"
        self._context = None
        self.set_band_step = set_band_step
        self.set_ready_step = set_ready_step
        self.pointing_step = pointing_step
        self.exec_settings = None

    def set_stackable_context(self, context: StackableContext):
        self.pointing_step.set_stackable_context(context)

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
        band: BandType = "B2"
        # use dummy source position as it is not implemented yet
        source = SourcePosition(10.0, 10.0)
        clear_supscription_specs()
        configure_band_to_finish = self.set_band_step.set_wait_for_do(band, dish_ids)
        with wait_for(configure_band_to_finish, timeout=100, live_logging=True):
            self.set_band_step.do(band, dish_ids)
        clear_supscription_specs()
        # then we set it to operational
        set_ready_to_finish = self.set_ready_step.set_wait_for_do(dish_ids)
        with wait_for(set_ready_to_finish, timeout=100, live_logging=True):
            self.set_ready_step.do(dish_ids)
        clear_supscription_specs()
        set_pointing_to_start = self.pointing_step.set_wait_for_do(dish_ids)
        with wait_for(set_pointing_to_start, timeout=100, live_logging=True):
            self.pointing_step.do(dish_ids, source)

    def undo(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in Dish.

        This implments the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        clear_supscription_specs()
        undo_pointing = self.pointing_step.set_wait_for_undo(
            self.pointing_step.configured_dishes
        )
        with wait_for(undo_pointing, timeout=30, live_logging=True):
            self.pointing_step.undo()
        clear_supscription_specs()
        undo_set_ready = self.set_ready_step.set_wait_for_undo()
        with wait_for(undo_set_ready, timeout=30, live_logging=True):
            self.set_ready_step.undo()
        clear_supscription_specs()
        undo_configure_band = self.set_band_step.set_wait_for_undo()
        with wait_for(undo_configure_band, timeout=30, live_logging=True):
            self.set_band_step.undo()

    def set_wait_for_do(
        self, sub_array_id: int, receptors: List[int]
    ) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for configuring a scan is done.

        :param sub_array_id: The index id of the subarray to control
        """
        return get_message_board_builder()

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
        return get_message_board_builder()


class DishEntryPoint(CompositeEntryPoint):
    """Derived Entrypoint scoped to Dish element."""

    _dishes_assigned = [1, 2, 3, 4]

    def __init__(self) -> None:
        """Init Object"""
        super().__init__()
        self.set_online_step = NoOpStep()
        self.start_up_step = NoOpStep()
        self.assign_resources_step = DishAssignStep()
        self.set_band_step = SetBandStep()
        self.set_ready_step = SetReadyStep()
        self.pointing_step = PointingStep()
        self.configure_scan_step = DishConfigureStep(
            self.set_band_step, self.set_ready_step, self.pointing_step
        )
        self.scan_step = cast(ScanStep, NoOpStep())

    def set_stackable_context(self, context: StackableContext):
        cast(DishConfigureStep, self.configure_scan_step).set_stackable_context(context)

    @property
    def dishes_to_assign(self) -> list[int]:
        return cast(DishAssignStep, self.assign_resources_step).dishes_to_assign

    @dishes_to_assign.setter
    def dishes_to_assign(self, receptors: list[int]):
        configure_scan_step = cast(DishAssignStep, self.assign_resources_step)
        configure_scan_step.dishes_to_assign = receptors
