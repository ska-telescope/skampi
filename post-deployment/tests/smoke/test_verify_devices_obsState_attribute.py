"""
The LMC base classes now implement a state machine with changes to the enum labels
of the obsState attribute. This test ensures that all devices have the same labels
and values
"""
import pytest
from tango import Database, DeviceProxy

# obsState enums as defined in lmc base classes control model
obs_state_enums = ("IDLE", "CONFIGURING", "READY", "SCANNING", "PAUSED", "ABORTED", "FAULT")
default_tango_server_classes = ('DataBase', 'DServer', 'Starter', 'TangoAccessControl')


def _remove_special_characters_from_enum_labels(enum_labels):
    for idx, label in enumerate(enum_labels):
        new_label = ''.join(char for char in label if char.isalnum())
        enum_labels[idx] = new_label.upper()
    return enum_labels

def is_enum_labels_valid(enum_labels):
    """verfiy enum labels have the right length, correct names and order"""
    formatted_enum_labels = _remove_special_characters_from_enum_labels(enum_labels)
    label_order_correctness = []
    # First check
    if len(formatted_enum_labels) != len(obs_state_enums):
        return False

    for idx, label in enumerate(formatted_enum_labels):
        try:
            # Second check
            true_index = obs_state_enums.index(label)
        except ValueError:
            return False
        else:
            label_order_correctness.append(true_index==idx)
    # Third check
    return all(label_order_correctness)


@pytest.mark.fast
def test_obs_state_attribute_enum_labels_are_valid():
    db = Database()
    server_classes = db.get_class_list('*')
    defaulting_classes = []

    for server_class in server_classes:
        if server_class in default_tango_server_classes:
            continue
        device_names = db.get_device_exported_for_class(server_class)
        # List of devices implementing the same server class will have the same
        # interface/implementation. Hence, use only one device for the test
        device_name = device_names[0]
        dp = DeviceProxy(device_name)
        attribute_list = dp.get_attribute_list()
        if "obsState" not in attribute_list:
            continue
        enum_labels = dp.get_attribute_config("obsState").enum_labels
        if not is_enum_labels_valid(enum_labels):
            defaulting_classes.append(server_class)

    msg = f"Classes ({defaulting_classes}) don't have a conforming obsState enum labels/values"
    assert len(defaulting_classes) == 0, msg
