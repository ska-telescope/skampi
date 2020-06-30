"""
The LMC base classes now implement a state machine with changes to the enum labels
of the obsState attribute. This test ensures that all devices have the same labels
and values
"""
import logging
import pytest
from random import shuffle
from tango import Database, DeviceProxy

# obsState enum as defined in lmc-base-classes 0.5.4 control model
obs_state_enum = ("IDLE", "CONFIGURING", "READY", "SCANNING", "PAUSED", "ABORTED", "FAULT")
default_tango_server_classes = ('DataBaseds', 'DServer', 'Starter',
                                'TangoAccessControl', 'TangoRestServer')


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
    if len(formatted_enum_labels) != len(obs_state_enum):
        return False

    for idx, label in enumerate(formatted_enum_labels):
        try:
            # Second check
            true_index = obs_state_enum.index(label)
        except ValueError:
            return False
        else:
            label_order_correctness.append(true_index==idx)
    # Third check
    return all(label_order_correctness)

@pytest.fixture(scope="function")
def extract_enums():
    """Query the database and retrieve enum labels for classes with
    obsState attribute in their device"""
    devices_and_enums = {}
    db = Database()
    server_instances = db.get_server_list()

    for server_instance in server_instances:
        server = server_instance.split("/")[0]
        if server in default_tango_server_classes:
            continue
        devices_and_classes = db.get_device_class_list(server_instance)
        for val in devices_and_classes:
            if not(val.lower().startswith('dserver') or len(val.split("/"))==1):
                dp = DeviceProxy(val)
                attribute_list = dp.get_attribute_list()
                if "obsState" not in attribute_list:
                    continue
                enum_labels = dp.get_attribute_config("obsState").enum_labels
                # cast label from tango._tango.StdStringVector to List
                enum_labels = list(enum_labels)
                devices_and_enums[val] = enum_labels

    return devices_and_enums


@pytest.mark.fast
def test_obs_state_attribute_for_invalid_enum_labels(extract_enums):
    extracted_enums = extract_enums
    # use only the first value from the dict
    selected_enum_labels = next(iter(extracted_enums.values()))

    # check for right length
    bigger_list = selected_enum_labels + selected_enum_labels[:]
    logging.info(f"Verify there are more than {len(obs_state_enum)} elements in {bigger_list}")
    assert is_enum_labels_valid(bigger_list) == False

    smaller_list = selected_enum_labels[0:4]
    logging.info(f"Verify there are less than {len(obs_state_enum)} elements in {smaller_list}")
    assert is_enum_labels_valid(bigger_list) == False

    # check for same names
    correct_lbl = selected_enum_labels[0]
    selected_enum_labels[0] = "attr_1"
    logging.info(f"Verify labels in {selected_enum_labels} differ from labels in {obs_state_enum}")
    assert is_enum_labels_valid(selected_enum_labels) == False
    # restore the correct label
    selected_enum_labels[0] = correct_lbl

    # check for correct order
    shuffle(selected_enum_labels)
    logging.info(f"Verify labels in {selected_enum_labels} do not conform to the obsState attribute"
                 f" labels in {obs_state_enum}")
    assert is_enum_labels_valid(selected_enum_labels) == False

@pytest.mark.fast
def test_obs_state_attribute_enum_labels_are_valid(extract_enums):
    extracted_enums = extract_enums
    defaulting_devices = []
    for device, enum_labels in extracted_enums.items():
        if not is_enum_labels_valid(enum_labels):
                defaulting_devices.append(device)

    logging.info(f"Enum labels for {len(extracted_enums.keys())} devices were checked for"
                 f" conformity with labels in {obs_state_enum}")
    msg = f"Devices ({defaulting_devices}) don't have a conforming obsState enum labels"
    assert len(defaulting_devices) == 0, msg
