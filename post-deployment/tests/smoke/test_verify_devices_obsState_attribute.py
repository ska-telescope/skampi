"""
The LMC base classes now implement a state machine with changes to the enum labels
of the obsState attribute. This test ensures that all devices have the same labels
and values
"""
import pytest
from tango import Database, DeviceProxy

# obsState enums as defined in lmc base class control model
obs_state_enums = ["IDLE", "CONFIGURING", "READY", "SCANNING", "PAUSED", "ABORTED", "FAULT"]

def _is_label_conformant(enum_labels):
    label_order_correctness = []
    for idx, label in enumerate(enum_labels):
        try:
            true_index = obs_state_enums.index(label)
        except ValueError:
            return False
        else:
            label_order_correctness.append(true_index==idx)
    return all(label_order_correctness)


def is_enum_valid(device_name):
    dp = DeviceProxy(device_name)
    attr_list = dp.get_attribute_list()

    # skip all devices w/o obsState attribute
    if "obsState" not in attr_list:
        return True

    # skip checking for enums with less or more values
    enum_labels = dp.get_attribute_config("obsState").enum_labels
    if len(enum_labels) != len(obs_state_enums):
        return False

    # remove all special charaters from labels
    for idx, label in enumerate(enum_labels):
        new_label = ''.join(char for char in label if char.isalnum())
        enum_labels[idx] = new_label.upper()

    return _is_label_conformant(enum_labels)

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
                if not is_enum_valid(val):
                    defaulting_devices.append(val)

    msg = f"Devices ({defaulting_devices} don't have conforming obsState enum labels/values"
    assert len(defaulting_devices) == 0, msg
