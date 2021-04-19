"""
The LMC base classes now implement a state machine with changes to the enum labels
of the obsState attribute. This test ensures that all devices have the same labels
and values
"""
import logging
import pytest
from collections import defaultdict
from random import shuffle
from tango import Database, DeviceProxy, DevFailed # type: ignore
import os

DEV_TEST_TOGGLE = os.environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True

def _remove_special_characters_from_enum_labels(enum_labels):
    for idx, label in enumerate(enum_labels):
        new_label = ''.join(char for char in label if char.isalnum())
        enum_labels[idx] = new_label.upper()
    return enum_labels

@pytest.fixture(scope="function")
def device_enum_labels_map():
    """Query the database and retrieve enum labels for devices with
    obsState attribute in their device"""
    devices_and_enums = {}
    db = Database()
    device_names = db.get_device_exported("*")

    for dev_name in device_names:
        dp = DeviceProxy(dev_name)
        attribute_list = dp.get_attribute_list()
        # skip all devices without the obsState attribute
        if "obsState" not in attribute_list:
            continue
        enum_labels = dp.get_attribute_config("obsState").enum_labels
        # cast label from tango._tango.StdStringVector to List
        enum_labels = list(enum_labels)
        formatted_enum_labels = _remove_special_characters_from_enum_labels(enum_labels)
        devices_and_enums[dev_name] = formatted_enum_labels

    return devices_and_enums

@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
@pytest.mark.fast
@pytest.mark.skamid
def test_obs_state_attribute_for_different_enum_labels(device_enum_labels_map):
    selected_enum_labels = list(device_enum_labels_map.values())[0]
    list_of_enums = [selected_enum_labels[:] for _ in range(3)]
    enum_variations = set()

    def perform_check(list_of_enums, msg):
        for enum_labels in list_of_enums:
            enum_variations.add(tuple(enum_labels))
        logging.info(f"{msg}: {enum_variations}")
        assert len(enum_variations) == 2
        enum_variations.clear()

    # check for different length
    list_of_enums[0].append("new_label") # add one more label to first list
    msg = "Verify two enum variations are detected due to different sizes"
    perform_check(list_of_enums, msg)
    list_of_enums[0].pop()

    # check for same length but different names
    list_of_enums[0][0] = "new_label" # change a label in first list
    msg = "Verify two enum variations are detected due to different names"
    perform_check(list_of_enums, msg)

    # check for lists with different order
    list_of_enums.pop(0) # remove first list
    # shuffle labels in each list
    for enum_labels in list_of_enums:
        shuffle(enum_labels)
    msg = "Verify two enum variations are detected due to different order"
    perform_check(list_of_enums, msg)

@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
@pytest.mark.fast
@pytest.mark.skamid
def test_obs_state_attribute_enum_labels_are_the_same(device_enum_labels_map):
    enum_variations = defaultdict(list)

    for device, enum_labels in device_enum_labels_map.items():
        # Keys are the labels. Value is a list of device names
        enum_variations[tuple(enum_labels)].append(device)

    for labels, device_list in enum_variations.items():
        logging.info(f"Devices {device_list} has obsState enum labels: {labels}\n")

    assert len(enum_variations) == 1, "ObsState enum labels vary for some devices"
