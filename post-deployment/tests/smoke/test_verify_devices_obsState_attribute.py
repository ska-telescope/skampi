"""
The LMC base classes now implement a state machine with changes to the enum labels
of the obsState attribute. This test ensures that all devices have the same labels
and values
"""
from tango import Database, DeviceProxy
import pytest

def _is_enum_valid(device_name):
    dp = DeviceProxy(device_name)
    # do some checks
    return

@pytest.mark.fast
def test_check_obs_state_enum():
    db = Database()
    server_list = db.get_server_list()

    i = 0
    defaulting_devices = []

    while i < len(server_list):
        class_list = db.get_device_class_list(server_list[i])
        j = 0
        while j < len(class_list):
            temp = class_list[j].split("/")
            if all([len(temp) != 1, "dserver" not in temp]):
                if not _is_enum_valid(class_list[j]):
                    defaulting_devices.append(class_list[j])
            j += 2
        i += 1

    msg = f"Devices ({defaulting_devices} don't have confirming obsState enum labels/values"
    assert len(defaulting_devices) == 0, msg
