from typing import Union

from resources.models.obsconfig.config import Observation
from ska_ser_skallop.mvp_control.configuration.types import (
    ScanConfiguration,
    ScanConfigurationType,
)


class SKAObservation:
    def __init__(self, observation: Observation) -> None:
        self.observation = observation
        self.next_target_id: Union[str, None] = None

    def set_next_target_to_be_configured(self, target: str):
        self.next_target_id = target

    def generate_sdp_scan_config(self):
        return self.observation.generate_sdp_scan_config(self.next_target_id)


class SKAScanConfiguration(ScanConfiguration, SKAObservation):
    def __init__(self, observation: Observation) -> None:
        conf_type = ScanConfigurationType.STANDARD
        super().__init__(conf_type)
        SKAObservation.__init__(self, observation)
