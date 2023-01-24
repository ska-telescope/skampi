from typing import Any, Literal, TypedDict

from ska_tmc_cdm.messages.central_node.common import DishAllocation
from ska_tmc_cdm.messages.subarray_node.configure.core import (
    DishConfiguration,
    PointingConfiguration,
)

from .target_spec import TargetSpecs

ReceptorName = Literal[
    "SKA0001",
    "SKA0002",
    "SKA0003",
    "SKA0004",
    "SKA0005",
    "SKA0006",
    "SKA0007" "SKA0008" "SKA0009",
]


class ResourceConfiguration(TypedDict):
    receptors: list[ReceptorName]


class Dishes(TargetSpecs):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.dish_specs: dict[str, list[ReceptorName]] = {
            "two": ["SKA0001", "SKA0002"],
            "three": ["SKA0001", "SKA0002", "SKA0003"],
            "four": ["SKA0001", "SKA0002", "SKA0003", "SKA0004"],
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
        adapted_dishes = [dish.replace("SKA", "") for dish in self.dishes]
        return DishAllocation(adapted_dishes)

    @property
    def resource_configuration(self):
        return ResourceConfiguration(receptors=self.dishes)

    def get_pointing_configuration(self, target_id: str | None = None):
        return PointingConfiguration(self.get_target_spec(target_id).target)

    def get_dish_configuration(self, target_id: str | None = None):
        return DishConfiguration(self.get_target_spec(target_id).band)
