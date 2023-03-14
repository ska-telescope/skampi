"""
Observation configuration to run the
SDP visibility receive script
"""
import json
import os
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

VIS_PARAMS_FILE = f"{os.path.dirname(os.path.abspath(__file__))}/../sdp_model/vis_rec_params.json"


def _load_json(json_file):
    with open(json_file) as file:
        parsed_json = json.load(file)
    return parsed_json


class VisRecObservation(Observation):
    """
    Observation object for the SDP visibility receive test.
    """
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.target_specs = VIS_REC_SPEC
        self.channel_configurations = VIS_REC_CHANNELS
        self.processing_specs = {
            "vis-receive": ProcessingSpec(
                script=VIS_RECEIVE_SCRIPT,
                parameters=_load_json(VIS_PARAMS_FILE))
            }
