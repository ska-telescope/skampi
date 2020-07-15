import os
import socket
import pytest

from tango import DeviceProxy
from tango_simlib.utilities.validate_device import validate_device_from_url

SPEC_URLS = {
    "ska_tango_guide_ska_wide": (
        "https://gitlab.com/ska-telescope/telescope-model/-/raw/SAR-114/"
        "Create-a-minimal-spec-for-TM-DSH-interface/tango_device_specifications/"
        "ska_wide/ska_tango_guide_ska_wide.yaml"
    )
}

SPECS_TO_CHECK = {"ska_tango_guide_ska_wide": ("mid_d0001/elt/master",)}


@pytest.mark.fast
def test_device_conforms_to_spec():
    """Run through all the specifications and the devices against which to test them"""
    for spec, devices in SPECS_TO_CHECK.items():
        for test_device in devices:
            result = validate_device_from_url(test_device, SPEC_URLS[spec], False)
            assert not result, (
                "Device [{}] with specification from [{}] has the following"
                " differences:\n{}"
            ).format(test_device, SPEC_URLS[spec], result)
