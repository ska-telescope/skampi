from typing import Any, Literal, TypedDict

from ska_tmc_cdm.messages.central_node.common import DishAllocation
from ska_tmc_cdm.messages.subarray_node.configure.core import (
    DishConfiguration,
    PointingConfiguration,
)

from .target_spec import TargetSpecs

ReceptorName = Literal[
    "SKA001",
    "SKA002",
    "SKA003",
    "SKA004",
    "SKA005",
    "SKA006",
    "SKA007",
    "SKA008",
    "SKA009",
]


class ResourceConfiguration(TypedDict):
    receptors: list[ReceptorName]


class Dishes(TargetSpecs):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.dish_specs: dict[str, list[ReceptorName]] = {
            "two": ["SKA001", "SKA002"],
            "three": ["SKA001", "SKA002", "SKA003"],
            "four": ["SKA001", "SKA002", "SKA003", "SKA004"],
            # vis-receive script doesn't allow the above resources
            # in the current visibility-receive test because it is running
            # for Low, and the above names are for Mid dishes,
            # while below we have Low station names.
            # TODO: set up the testing infrastructure to properly
            #  distinguish between Mid and Low
            #  (see tests/resources/models/obsconfig/vis_receive_config.py)
            "vis-rec": ["C10", "C136", "C1", "C217", "C13", "C42"],
        }

    @property
    def dishes(self) -> list[ReceptorName]:
        return list(
            {
                dish
                for target in self.target_specs.values()
                for dish in self.dish_specs[target.dishes]
            }
        )

    @property
    def dish_allocation(self):
        adapted_dishes = [dish for dish in self.dishes]
        return DishAllocation(adapted_dishes)

    @property
    def resource_configuration(self):
        return ResourceConfiguration(receptors=self.dishes)

    def get_pointing_configuration(self, target_id: str | None = None):
        return PointingConfiguration(self.get_target_spec(target_id).target)

    def get_dish_configuration(self, target_id: str | None = None):
        return DishConfiguration(self.get_target_spec(target_id).band)
