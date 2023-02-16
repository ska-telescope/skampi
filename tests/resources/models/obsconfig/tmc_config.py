from datetime import timedelta

from ska_tmc_cdm.messages.subarray_node.configure import TMCConfiguration


class TmcConfig:
    def generate_tmc_scan_config(self, scan_duration: float):
        scan_duration = timedelta(seconds=10)
        tmc_config = TMCConfiguration(scan_duration=scan_duration)
        return tmc_config
