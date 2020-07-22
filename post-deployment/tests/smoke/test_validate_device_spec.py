import os
import socket
import pytest

from tango import DeviceProxy
from tango_simlib.utilities.validate_device import validate_device_from_url

SPEC_URLS = {
    "ska_tango_guide_ska_wide": (
        "https://gitlab.com/ska-telescope/telescope-model/-/raw/"
        "master/spec/tango/ska_wide/Guidelines.yaml"
    ),
    "dish_master": (
        "https://gitlab.com/ska-telescope/telescope-model/-/raw/"
        "master/spec/tango/dsh/DishMaster.yaml"
    )
}

SPECS_TO_CHECK = {"ska_tango_guide_ska_wide": ("mid_d0001/elt/master",),
                  "dish_master": ("mid_d0001/elt/master",)}


@pytest.mark.fast
def test_device_conforms_to_spec():
    """Run through all the specifications and the devices against which to test them"""
    for spec, devices in SPECS_TO_CHECK.items():
        for test_device in devices:
            print("\nChecking device {} against {}".format(test_device, spec))
            result = validate_device_from_url(test_device, SPEC_URLS[spec], False)
            # Printing differences for now, rather than asserting
            print("Differences:\n{}".format(result))
