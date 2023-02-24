"""Domain logic for the Dish."""
import abc
import logging
from typing import Dict, Literal, Union, List, cast
import os


from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_fixtures.context_management import StackableContext
from ska_ser_skallop.mvp_control.event_waiting.wait import wait_for
from ska_ser_skallop.utils.singleton import Memo
from ska_ser_skallop.mvp_fixtures.base import ExecSettings

from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    NoOpStep,
    MessageBoardBuilder,
    ScanStep,
    AssignResourcesStep,
)
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.event_handling.builders import (
    get_message_board_builder,
    clear_supscription_specs,
)
from ..obsconfig.config import Observation

from .dish_pointing import Pointing, SourcePosition, start_as_cm, stop, start


logger = logging.getLogger(__name__)


class LogEnabled:
    """class that allows for logging if set by env var"""

    def __init__(self) -> None:
        self._live_logging = bool(os.getenv("DEBUG_ENTRYPOINT"))
        self._skamid = cast(names.Mid, names.TEL().skamid)
        assert self._skamid, "wrong telescope, this is Mid only"

    def _log(self, mssage: str):
        if self._live_logging:
            logger.info(mssage)


class StartupDishes(base.ObservationStep, LogEnabled):
    """Implementation of power up Step for dishes."""

    def __init__(self, dish_ids: list[int]) -> None:
        """Init object."""
        super().__init__()
        self._skamid = cast(names.Mid, names.TEL().skamid)
        assert self._skamid, "wrong telescope, this is Mid only"
        self.dish_ids = dish_ids

    def do(self):  # type: ignore
        """Domain logic for startung up dishes"""

        successfully_commanded_dishes: list[con_config.AbstractDeviceProxy] = []
        dish_names = self._skamid.dishes(self.dish_ids).list
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

    def undo(self):  # type: ignore
        """Domain logic for powering down all the dishes

        This implements the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        dish_names = self._skamid.dishes(self.dish_ids).list
        for dish_name in dish_names:
            dish = con_config.get_device_proxy(dish_name, fast_load=True)
            self._log(f"setting {dish_name} to SetStandbyLPMode")
            dish.command_inout("SetStandbyLPMode")

    def set_wait_for_do(self) -> MessageBoardBuilder:  # type: ignore
        """Domain logic specifying what needs to be waited for subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        brd = get_message_board_builder()
        dish_names = self._skamid.dishes(self.dish_ids).list
        for dish in dish_names:
            brd.set_waiting_on(dish).for_attribute("dishmode").to_become_equal_to(
                "STANDBY_FP", ignore_first=False
            )
        return brd

    def set_wait_for_doing(self) -> MessageBoardBuilder:  # type: ignore
        """Not implemented."""
        raise NotImplementedError()

    def set_wait_for_undo(self) -> MessageBoardBuilder:  # type: ignore
        """Domain logic specifying what needs to be waited for subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        brd = get_message_board_builder()
        dish_names = self._skamid.dishes(self.dish_ids).list
        for dish in dish_names:
            brd.set_waiting_on(dish).for_attribute("dishmode").to_become_equal_to(
                "STANDBY_LP", ignore_first=False
            )
        return brd


class AssignedDishes:
    @property
    @abc.abstractmethod
    def assigned_dishes(self) -> list[int]:
        pass


class DishAssignResourcesStep(AssignResourcesStep, AssignedDishes):
    def __init__(self, observation: Observation) -> None:
        """Init object."""
        super().__init__()
        self.observation = observation
        self._skamid = cast(names.Mid, names.TEL().skamid)
        assert self._skamid, "wrong telescope, this is Mid only"

    def do(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        composition: types.Composition,
        sb_id: str,
    ):
        self.assigned_dishes = dish_ids

    @property
    def assigned_dishes(self) -> list[int]:
        if dishes := Memo().get("assigned_dishes"):
            return cast(list[int], dishes)
        return []

    @assigned_dishes.setter
    def assigned_dishes(self, dish_ids: list[int]):
        Memo(assigned_dishes=dish_ids)

    def undo(self, sub_array_id: int):
        self.assigned_dishes = []

    def set_wait_for_do(self, sub_array_id: int) -> MessageBoardBuilder:
        return get_message_board_builder()

    def set_wait_for_undo(self, sub_array_id: int) -> MessageBoardBuilder:
        return get_message_board_builder()


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

    def __init__(self, assigned_dishes: AssignedDishes) -> None:
        super().__init__()
        self._assigned_dishes_object = assigned_dishes

    band_configure_mapping: Dict[BandType, BandConfigureCommand] = {
        "B1": "ConfigureBand1",
        "B2": "ConfigureBand2",
        "B3": "ConfigureBand3",
        "B4": "ConfigureBand4",
        "B5a": "ConfigureBand5a",
        "B5b": "ConfigureBand5b",
    }

    @property
    def assigned_dishes(self) -> list[int]:
        return self._assigned_dishes_object.assigned_dishes

    def do(self, band: BandType):
        """_summary_

        :param band: _description_
        :param _: _description_
        """
        successfully_commanded_dishes: list[con_config.AbstractDeviceProxy] = []
        dish_ids = self.assigned_dishes
        dish_name = ""
        try:
            for dish_name in self._skamid.dishes(dish_ids):
                dish = con_config.get_device_proxy(dish_name)
                command = self.band_configure_mapping[band]
                self._log(f"Commanding {dish_name} with {command}")
                # this myabe the future command dish.command_inout(command, " ")
                dish.command_inout(command)
        except Exception as exception:
            self._log(
                f"Exception in commanding {dish_name} will revert commands on other dishes"
            )
            for successfully_commanded_dish in successfully_commanded_dishes:
                successfully_commanded_dish.command_inout("SetStandbyLPMode")
            raise exception

    def set_wait_for_do(self, band: BandType) -> MessageBoardBuilder:
        """Get specifications of what to wait for in order for configure band to be complete.


        :return: _description_
        :rtype: Union[MessageBoardBuilder, None]
        """
        dish_ids = self.assigned_dishes
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


class ReadyDishes:
    @property
    @abc.abstractmethod
    def ready_dishes(self) -> list[names.DeviceName]:
        pass


class SetReadyStep(LogEnabled, ReadyDishes):
    """A 'sub' step specifically to ensure dish is ready for pointing.

    (must be preceded by a SetBandStep step)
    """

    def __init__(self, assigned_dishes: AssignedDishes) -> None:
        super().__init__()
        self._assigned_dishes_object = assigned_dishes
        self._assigned_brd: Union[MessageBoardBuilder, None] = None

    @property
    def assigned_dishes(self) -> list[int]:
        return self._assigned_dishes_object.assigned_dishes

    @property
    def ready_dishes(self) -> list[names.DeviceName]:
        if dishes := Memo().get("ready_dishes"):
            return dishes
        return []

    @ready_dishes.setter
    def ready_dishes(self, dishes: list[names.DeviceName]):
        Memo(ready_dishes=dishes)

    def do(self):
        """_summary_

        :param band: _description_
        :param dish_ids: _description_
        """
        dish_ids = self.assigned_dishes
        successfully_commanded_dishes: list[names.DeviceName] = []
        dish_name = ""
        try:
            for dish_name in self._skamid.dishes(dish_ids):
                dish = con_config.get_device_proxy(dish_name)
                self._log(f"Commanding {dish_name} with SetOperateMode")
                dish.command_inout("SetOperateMode")
                successfully_commanded_dishes.append(dish_name)
        except Exception as exception:
            self._log(
                f"Exception in commanding {dish_name} will revert commands on other dishes"
            )
            for dish_name in successfully_commanded_dishes:
                dish = con_config.get_device_proxy(dish_name)
                dish.command_inout("SetStandbyFPMode")
                if self._assigned_brd:
                    if self._assigned_brd.board:
                        self._assigned_brd.board.remove_all_subscriptions()
            raise exception
        self.ready_dishes = successfully_commanded_dishes

    def set_wait_for_do(self) -> MessageBoardBuilder:
        """Get specifications of what to wait for in order for configure band to be complete.


        :return: _description_
        :rtype: Union[MessageBoardBuilder, None]
        """
        dish_ids = self.assigned_dishes
        brd = get_message_board_builder()
        self._assigned_brd = brd
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
        for dish_name in self.ready_dishes:
            dish = con_config.get_device_proxy(dish_name)
            self._log(
                f"Reverting Operate state from {dish_name} by commanding it with SetStandbyFP"
            )
            dish.command_inout("SetStandbyFPMode")

    def set_wait_for_undo(self) -> MessageBoardBuilder:
        """Domain logic for what needs to be waited for switching the Dish off."""
        brd = get_message_board_builder()
        for dish_name in self.ready_dishes:
            brd.set_waiting_on(dish_name).for_attribute(
                "pointingstate"
            ).to_become_equal_to("NONE", ignore_first=False)
        for dish_name in self.ready_dishes:
            brd.set_waiting_on(dish_name).for_attribute("dishmode").to_become_equal_to(
                "STANDBY_FP", ignore_first=False
            )
        return brd


class PointingStep(LogEnabled):
    """ "A 'sub' step of configuration that realizes the pointing behavior on the dish."""

    def __init__(
        self,
        ready_dishes: ReadyDishes,
        context: Union[StackableContext, None] = None,
    ) -> None:
        """Init object."""
        super().__init__()
        self._context = context
        self._dish_ids = []
        self._ready_dishes = ready_dishes

    def set_stackable_context(self, context: StackableContext):
        self._context = context

    @property
    def configured_dishes(self) -> list[names.DeviceName]:
        if dishes := Memo().get("configured_dishes"):
            return dishes
        return []

    @configured_dishes.setter
    def configured_dishes(self, dishes: list[names.DeviceName]):
        Memo(configured_dishes=dishes)

    @property
    def _pointings(self) -> list[Pointing]:
        if pointings := Memo().get("_pointings"):
            return pointings
        return []

    @_pointings.setter
    def _pointings(self, pointings: list[Pointing]):
        Memo(_pointings=pointings)

    def do(self, source: SourcePosition, polling: float = 0.05):
        """_summary_

        :param dish_ids: _description_
        :param source: _description_
        :param polling: _description_, defaults to 0.05
        """

        self._log("starting pointing threads...")
        dishes = self._ready_dishes.ready_dishes
        if self._context:
            self._pointings = self._context.push_context_onto_test(
                start_as_cm(dishes, source, polling)
            )
        else:
            self._pointings = start(dishes, source, polling)
        self.configured_dishes = dishes

    def set_wait_for_do(self) -> MessageBoardBuilder:
        """_summary_

        :raises NotImplementedError: _description_
        :return: _description_
        :rtype: Union[MessageBoardBuilder, None]
        """
        brd = get_message_board_builder()
        # TODO currently there is a bug in that the pointing state
        # should end up as Track but we use READY as our indicator
        # until bug is fixed
        for dish in self._ready_dishes.ready_dishes:
            brd.set_waiting_on(dish).for_attribute("pointingstate").to_become_equal_to(
                "TRACK"
            )
        return brd

    def undo(self):
        self._log("stopping pointing threads...")
        stop(self._pointings)

    def set_wait_for_undo(self) -> MessageBoardBuilder:
        """_summary_

        :param dish_ids: _description_
        :type dish_ids: list[int]
        :return: _description_
        :rtype: Union[MessageBoardBuilder, None]
        """
        brd = get_message_board_builder()
        for dish in self.configured_dishes:
            brd.set_waiting_on(dish).for_attribute("pointingstate").to_become_equal_to(
                "READY"
            )
        return brd


class DishConfigureStep(base.ConfigureStep, LogEnabled):
    """Implementation of Configure Scan Step for Dish."""

    def __init__(
        self,
        assigned_dishes: AssignedDishes,
    ) -> None:
        """Init object."""
        super().__init__()
        self._skamid = names.TEL().skamid
        assert self._skamid, "wrong telescope, this is Mid only"
        self._context = None
        self.set_band_step = SetBandStep(assigned_dishes)
        self.set_ready_step = SetReadyStep(assigned_dishes)
        self.pointing_step = PointingStep(self.set_ready_step)
        self.exec_settings = None

    def set_stackable_context(self, context: StackableContext):
        self.pointing_step.set_stackable_context(context)

    @property
    def execution_context(self) -> ExecSettings:
        if global_execution_context := Memo().get("execution_context"):
            return global_execution_context
        return ExecSettings()

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
        timeout = int(self.execution_context.time_out)
        live_logging = self.execution_context.log_enabled
        clear_supscription_specs()
        configure_band_to_finish = self.set_band_step.set_wait_for_do(band)
        with wait_for(
            configure_band_to_finish, timeout=timeout, live_logging=live_logging
        ):
            self.set_band_step.do(band)
        clear_supscription_specs()
        # then we set it to operational
        set_ready_to_finish = self.set_ready_step.set_wait_for_do()
        with wait_for(set_ready_to_finish, timeout=timeout, live_logging=live_logging):
            self.set_ready_step.do()
        clear_supscription_specs()
        set_pointing_to_start = self.pointing_step.set_wait_for_do()
        with wait_for(
            set_pointing_to_start, timeout=timeout, live_logging=live_logging
        ):
            self.pointing_step.do(source)

    def undo(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in Dish.

        This implments the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        clear_supscription_specs()
        undo_pointing = self.pointing_step.set_wait_for_undo()
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


def set_execution_context(execution_context: ExecSettings):
    Memo(execution_context=execution_context)


class DishEntryPoint(CompositeEntryPoint, AssignedDishes):
    """Derived Entrypoint scoped to Dish element."""

    nr_of_dishes = [1, 2, 3, 4]

    def __init__(self, observation: Observation | None = None) -> None:
        """Init Object"""
        super().__init__()
        if not observation:
            if not (observation := Memo().get("dish_entry_point__observation")):
                observation = Observation()
                Memo(dish_entry_point__observation=observation)
        self.set_online_step = NoOpStep()
        self.start_up_step = StartupDishes(self.nr_of_dishes)
        self.assign_resources_step = DishAssignResourcesStep(observation)
        self.configure_scan_step = DishConfigureStep(self.assign_resources_step)
        self.scan_step = cast(ScanStep, NoOpStep())

    def set_stackable_context(self, context: StackableContext):
        cast(DishConfigureStep, self.configure_scan_step).set_stackable_context(context)

    @property
    def assigned_dishes(self) -> list[int]:
        return cast(DishAssignResourcesStep, self.assign_resources_step).assigned_dishes
