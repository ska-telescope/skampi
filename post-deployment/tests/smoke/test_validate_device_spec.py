import logging

from tempfile import NamedTemporaryFile

import requests
import pytest

from tango import Database # type: ignore
from tango_simlib.utilities.validate_device import (
    validate_device_from_path,
    validate_device_from_url,
)

SPEC_URLS = {
    "ska_tango_guide_ska_wide": (
        "https://gitlab.com/ska-telescope/telescope-model/-/raw/"
        "master/spec/tango/ska_wide/Guidelines.yaml"
    ),
    "dish_master": (
        "https://gitlab.com/ska-telescope/telescope-model/-/raw/"
        "master/spec/tango/dsh/DishMaster.yaml"
    ),
}


def check_mid_low(device_name):
    """Check if a device domain contains mid or low"""
    domain, *_ = device_name.split("/")
    if "mid" in domain or "low" in domain:
        return True
    return False


@pytest.mark.xfail(reason="Not all SKA devices complies to spec at present")
@pytest.mark.skamid
def test_ska_devices():
    """Check SKA devices against the Tango developers guide."""
    devices = Database().get_device_exported("*")
    devices = list(filter(check_mid_low, devices))

    test_result = {}
    with NamedTemporaryFile(mode="wb") as tmp_file:
        spec_response = requests.get(SPEC_URLS["ska_tango_guide_ska_wide"])
        tmp_file.write(spec_response.content)
        tmp_file.seek(0)

        for device in devices:
            result = validate_device_from_path(device, tmp_file.name, False)
            if result:
                test_result.setdefault(result, []).append(device)

    logging.info(
        "Checked %s devices against spec, %s\n",
        len(devices),
        SPEC_URLS["ska_tango_guide_ska_wide"],
    )
    for result, devices in test_result.items():
        logging.info(">>> Devices %s\nHave the following issues:\n%s\n", devices, result)

    assert not test_result.keys()


@pytest.mark.skamid
def test_dishmaster_conforms_to_tango_wide():
    """Check that dishmaster conforms to tango developers guide"""
    result = validate_device_from_url(
        "mid_d0001/elt/master", SPEC_URLS["ska_tango_guide_ska_wide"], False
    )
    assert not result


@pytest.mark.skamid
def test_dishmaster_conforms_to_dishmaster_spec():
    """Check that dishmaster device conforms to dishmaster specification"""
    result = validate_device_from_url("mid_d0001/elt/master", SPEC_URLS["dish_master"], False)
    assert not result
