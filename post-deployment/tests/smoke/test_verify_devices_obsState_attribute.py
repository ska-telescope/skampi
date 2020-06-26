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
    servers = db.get_server_list()
    defaulting_devices = []

    for server in servers:
        devices_and_classes = db.get_device_class_list(server)
        for val in devices_and_classes:
            # ignore classes and grab only devices which are not in the dserver domain
            if not(val.lower().startswith('dserver') or len(val.split("/"))==1):
                if not _is_enum_valid(val):
                    defaulting_devices.append(val)

    msg = f"Devices ({defaulting_devices} don't have conforming obsState enum labels/values"
    assert len(defaulting_devices) == 0, msg
