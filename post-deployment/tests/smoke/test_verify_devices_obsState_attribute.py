"""
The LMC base classes now implement a state machine with changes to the enum labels
of the obsState attribute. This test ensures that all devices have the same labels
and values
"""
import logging
import pytest
from random import shuffle
from tango import Database, DeviceProxy, DevFailed

# obsState enum as defined in lmc-base-classes 0.5.4 control model
obs_state_enum = ("IDLE", "CONFIGURING", "READY", "SCANNING", "PAUSED", "ABORTED", "FAULT")

def _remove_special_characters_from_enum_labels(enum_labels):
    for idx, label in enumerate(enum_labels):
        new_label = ''.join(char for char in label if char.isalnum())
        enum_labels[idx] = new_label.upper()
    return enum_labels


def is_enum_labels_valid(enum_labels):
    """verfiy enum labels have the right length, correct names and order"""
    formatted_enum_labels = _remove_special_characters_from_enum_labels(enum_labels)
    return formatted_enum_labels == list(obs_state_enum)


@pytest.fixture(scope="function")
def device_enum_labels_map():
    """Query the database and retrieve enum labels for devices with
    obsState attribute in their device"""
    devices_and_enums = {}
    db = Database()
    device_names = db.get_device_name("*", "*")

    for dev_name in device_names:
        if not(dev_name.lower().startswith('dserver') or len(dev_name.split("/")) == 1):
            dp = DeviceProxy(dev_name)
            try:
                attribute_list = dp.get_attribute_list()
            except DevFailed:
                # Skip devices (from the default tango server classes) which are not exported
                continue
            # skip all devices without the obsState attribute
            if "obsState" not in attribute_list:
                continue
            enum_labels = dp.get_attribute_config("obsState").enum_labels
            # cast label from tango._tango.StdStringVector to List
            enum_labels = list(enum_labels)
            devices_and_enums[dev_name] = enum_labels

    return devices_and_enums


@pytest.mark.fast
def test_obs_state_attribute_for_invalid_enum_labels(device_enum_labels_map):
    # use only the first value from the dict
    selected_enum_labels = next(iter(device_enum_labels_map.values()))

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
def test_obs_state_attribute_enum_labels_are_valid(device_enum_labels_map):
    enum_variations = set()
    for device, enum_labels in device_enum_labels_map.items():
        formatted_enum_labels = _remove_special_characters_from_enum_labels(enum_labels)
        enum_variations.add(tuple(formatted_enum_labels))
        logging.info(f"Device: {device}, enum labels: {formatted_enum_labels}.")

    msg = f"ObsState enum labels varies for some devices. The enum variations: {enum_variations}"
    assert len(enum_variations) == 1, msg
