"""
Observation configuration to run the
SDP visibility receive script
"""

from collections import OrderedDict
from typing import Any

from ska_tmc_cdm.messages.central_node.sdp import ScriptConfiguration
from ska_tmc_cdm.messages.subarray_node.configure.core import Target, ReceiverBand

from resources.models.obsconfig import Observation
from resources.models.obsconfig.channelisation import DEFAULT_CHANNELS
from resources.models.obsconfig.sdp_config import ProcessingSpec
from resources.models.obsconfig.target_spec import TargetSpec

VIS_RECEIVE_SCRIPT = ScriptConfiguration(
    kind="realtime", name="vis-receive", version="0.8.0"
)
VIS_REC_SPEC = OrderedDict(
    {
        "target:a": TargetSpec(
            Target("12:29:06.699 degrees", "02:03:08.598 degrees"),
            "target:a",
            ReceiverBand.BAND_2,  # how to set this for low?
            "vis_channels",
            "all",
            "field_a",
            "vis-receive",
            "vis-rec",
        ),
        ".default": TargetSpec(
            Target("12:29:06.699 degrees", "02:03:08.598 degrees"),
            ".default",
            ReceiverBand.BAND_2,
            "vis_channels",
            "all",
            "field_a",
            "vis-receive",
            "vis-rec",  # the type / number of dishes in tests.resources.models.obsconfig.dishes.Dishes
        ),
    }
)
VIS_REC_CHANNELS = DEFAULT_CHANNELS.copy()
VIS_REC_CHANNELS["vis_channels"].spectral_windows[0].count = 13824


class VisRecObservation(Observation):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.target_specs = VIS_REC_SPEC
        self.channel_configurations = VIS_REC_CHANNELS
        self.processing_specs = {"vis-receive": ProcessingSpec(
            script=VIS_RECEIVE_SCRIPT,
            parameters={
                "image": "artefact.skao.int/ska-sdp-realtime-receive-modules",
                "version": "3.6.0",
                "plasmaEnabled": "true",
                "reception": {
                    "layout": "/mnt/data/low-layout.json",
                    "num_channels": 13824,
                    "channels_per_stream": 6912,
                    "continuous_mode": "true",
                    "transport_protocol": "tcp",
                    "payloads_in_flight": 3,
                    "disable_astropy_iers_autodownload": "true",
                },
                "pvc": {"name": "shared"},
                "plasma_parameters": {
                    "initContainers": [
                        {
                            "name": "existing-output-remover",
                            "image": "artefact.skao.int/ska-sdp-realtime-receive-processors:0.4.0",
                            "command": ["rm", "-rf", "/mnt/data/output*.ms"],
                            "volumeMounts": [
                                {"mountPath": "/mnt/data", "name": "shared"}
                            ],
                        },
                        {
                            "name": "start-telmodel",
                            "image": "python:3.10-slim",
                            "command": [
                                "/bin/bash",
                                "-c",
                                "pip install --extra-index-url=https://artefact.skao.int/repository/pypi-internal/simple ska-telmodel==1.4.1 pyyaml; rm -f /mnt/data/low-layout.json ; ska-telmodel cat instrument/ska1_low/layout/low-layout.json > /mnt/data/low-layout.json",
                            ],
                            "volumeMounts": [
                                {"mountPath": "/mnt/data", "name": "shared"}
                            ],
                        },
                    ],
                    "extraContainers": [
                        {
                            "name": "plasma-processor",
                            "image": "artefact.skao.int/ska-sdp-realtime-receive-processors:0.4.0",
                            "args": [
                                "--max-payloads",
                                "12",
                                "--readiness-file",
                                "/tmp/processor_ready",
                                "output.ms",
                            ],
                            "volumeMounts": [
                                {
                                    "name": "plasma-storage-volume",
                                    "mountPath": "/plasma",
                                },
                                {"mountPath": "/mnt/data", "name": "shared"},
                            ],
                            "readinessProbe": {
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5,
                                "exec": {"command": ["cat", "/tmp/processor_ready"]},
                            },
                        }
                    ],
                },
            },
        )}
