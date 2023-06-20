"""
Observation configuration to run the
SDP visibility receive script
"""
import json
import os
from collections import OrderedDict
from typing import Any

from resources.models.obsconfig import Observation
from resources.models.obsconfig.channelisation import DEFAULT_CHANNELS
from resources.models.obsconfig.sdp_config import ProcessingSpec
from resources.models.obsconfig.target_spec import BaseTargetSpec, ArraySpec
from ska_tmc_cdm.messages.central_node.sdp import ScriptConfiguration
from ska_tmc_cdm.messages.subarray_node.configure.core import ReceiverBand, Target

VIS_RECEIVE_SCRIPT = ScriptConfiguration(kind="realtime", name="vis-receive", version="1.0.0")

# The current set up for the vis-receive test is a mish-mash of
# parameters for Mid and for Low. The code is set up to run
# receive for Low, but some of the underlying testing infrastructure
# in skampi doesn't allow proper distinguishing between Mid and Low,
# this includes using Low stations instead of Mid dishes.
# Below, VIS_REC_SPEC defines a "target_spec" which is based on the
# existing hard-coded versions in
# tests/resources/models/obsconfig/target_spec.py:23
# This means, some of the information is inaccurately used for Low data
# (e.g. referring to "dishes" instead of "stations", see comment in
# tests.resources.models.obsconfig.dishes.Dishes)
# TODO: GH will take a bit of time to update the test to be as accurate
#  with using telescope-specific data as possible and will look into
#  implementing proper station references instead of adding station names
#  to the dishes.py file.
VIS_REC_SPEC = OrderedDict(
    {
        "target:a": BaseTargetSpec(
            Target("12:29:06.699 degrees", "02:03:08.598 degrees"),
            "target:a",
            ReceiverBand.BAND_2,  # how to set this for low?
            "vis_channels",
            "all",
            "field_a",
            "vis-receive",
        ),
        ".default": BaseTargetSpec(
            Target("12:29:06.699 degrees", "02:03:08.598 degrees"),
            ".default",
            ReceiverBand.BAND_2,
            "vis_channels",
            "all",
            "field_a",
            "vis-receive",
            # below: the type / number of dishes in
            # tests.resources.models.obsconfig.dishes.Dishes
        ),
    }
)
ARRAY_SPEC = ArraySpec(receptors="two")

VIS_REC_CHANNELS = DEFAULT_CHANNELS.copy()
VIS_REC_CHANNELS["vis_channels"].spectral_windows[0].count = 13824


VIS_PARAMS_FILE = (
    f"{os.path.dirname(os.path.abspath(__file__))}" "/../sdp_model/vis_rec_params.json"
)


def _load_json(json_file):
    with open(json_file) as file:
        parsed_json = json.load(file)
    return parsed_json


class VisRecObservation(Observation):
    """
    Observation object for the SDP visibility receive test.
    """

    def __init__(self):
        super().__init__(
            base_target_specs=VIS_REC_SPEC,
            array=ARRAY_SPEC,
            processing_specs=[
                ProcessingSpec(
                script=VIS_RECEIVE_SCRIPT,
                parameters=_load_json(VIS_PARAMS_FILE),
            )
            ],
            channels=list(VIS_REC_CHANNELS.values())
        )
    
