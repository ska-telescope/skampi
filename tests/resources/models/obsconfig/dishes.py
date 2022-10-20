from typing import Any
from .target_spec import TargetSpecs
from ska_tmc_cdm.messages.central_node.common import DishAllocation
from ska_tmc_cdm.messages.central_node.sdp import ResourceConfiguration
from ska_tmc_cdm.messages.subarray_node.configure.core import (
    PointingConfiguration,
    DishConfiguration,
)


class Dishes(TargetSpecs):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.dish_specs = {
            "two": ["SKA0001", "SKA0002"],
            "three": ["SKA0001", "SKA0002", "SKA003"],
            "four": ["SKA0001", "SKA0002", "SKA003", "SKA004"],
        }

    @property
    def allocated_dishes(self) -> list[str]:
        return list(
            {
                dish
                for target in self.target_specs.values()
                for dish in self.dish_specs[target.dishes]
            }
        )

    def get_dish_allocation_from_target_spec(self):
        return DishAllocation(self.allocated_dishes)

    def get_dish_resource_allocation_from_target_spec(self):
        return ResourceConfiguration(receptors=self.allocated_dishes)

    def get_pointing_configuration(self, target_id: str | None = None):
        return PointingConfiguration(self.get_target_spec(target_id).target)

    def get_dish_configuration(self, target_id: str | None = None):
        return DishConfiguration(self.get_target_spec(target_id).band)
