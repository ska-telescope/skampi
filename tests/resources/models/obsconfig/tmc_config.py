from datetime import timedelta

from ska_tmc_cdm.messages.subarray_node.configure import TMCConfiguration


class TmcConfig:
    def generate_tmc_scan_config(self, scan_duration: float):
        return TMCConfiguration(timedelta(seconds=scan_duration))
