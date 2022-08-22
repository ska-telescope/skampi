import time

from tango import CmdArgType


def wait_for_change_on_resource(
    dev_proxy, attr_name, expected_val, timeout=120
):
    """Wait a while for a change in an attribute value"""
    checkpoint = timeout / 4
    start_time = time.time()
    time_elapsed = 0

    while time_elapsed <= timeout:
        current_val = retrieve_attr_value(dev_proxy, attr_name)
        # for progress attributes check for presence (in)
        if current_val == expected_val or expected_val in current_val:
            break

        if (time_elapsed % checkpoint) == 0:
            print(f"Waiting for {attr_name} to transition to {expected_val}")
            time.sleep(0.8 * checkpoint)
        time_elapsed = int(time.time() - start_time)


def retrieve_attr_value(dev_proxy, attr_name):
    """Get the attribute reading from device"""
    current_val = dev_proxy.read_attribute(attr_name)
    if current_val.type == CmdArgType.DevEnum:
        current_val = getattr(dev_proxy, attr_name).name
    elif current_val.type == CmdArgType.DevState:
        current_val = str(current_val.value)
    else:
        current_val = current_val.value
    return current_val
