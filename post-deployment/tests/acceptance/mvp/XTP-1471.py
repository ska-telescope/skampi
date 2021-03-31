# coding=utf-8
"""Default feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@scenario('features/XTP-1471.feature', 'PSI1.1 test, Successfully configure the subarray for a scan')
def test_psi11_test_successfully_configure_the_subarray_for_a_scan():
    """PSI1.1 test, Successfully configure the subarray for a scan."""


@scenario('features/XTP-1471.feature', 'PSI1.2 test, Subarray successfully completing a scan')
def test_psi12_test_subarray_successfully_completing_a_scan():
    """PSI1.2 test, Subarray successfully completing a scan."""


@given('a subarray with resources assigned')
def a_subarray_with_resources_assigned():
    """a subarray with resources assigned."""
    raise NotImplementedError


@given('the subarray is fully prepared to scan')
def the_subarray_is_fully_prepared_to_scan():
    """the subarray is fully prepared to scan."""
    raise NotImplementedError


@given('the subsystem Tango devices <devices> are in the IDLE obsState')
def the_subsystem_tango_devices_devices_are_in_the_idle_obsstate():
    """the subsystem Tango devices <devices> are in the IDLE obsState."""
    raise NotImplementedError


@given('the subsystem Tango devices <devices> are in the READY obsState')
def the_subsystem_tango_devices_devices_are_in_the_ready_obsstate():
    """the subsystem Tango devices <devices> are in the READY obsState."""
    raise NotImplementedError


@when('I send the Configure command from the user interface to the TMC SubarrayNode')
def i_send_the_configure_command_from_the_user_interface_to_the_tmc_subarraynode():
    """I send the Configure command from the user interface to the TMC SubarrayNode."""
    raise NotImplementedError


@when('I send the Scan command from the user interface to the TMC SubarrayNode')
def i_send_the_scan_command_from_the_user_interface_to_the_tmc_subarraynode():
    """I send the Scan command from the user interface to the TMC SubarrayNode."""
    raise NotImplementedError


@then('change to the READY state after the subarray completed the scan')
def change_to_the_ready_state_after_the_subarray_completed_the_scan():
    """change to the READY state after the subarray completed the scan."""
    raise NotImplementedError


@then('change to the READY state after the subarray is fully prepared to scan')
def change_to_the_ready_state_after_the_subarray_is_fully_prepared_to_scan():
    """change to the READY state after the subarray is fully prepared to scan."""
    raise NotImplementedError


@then('produce a valid measurement set')
def produce_a_valid_measurement_set():
    """produce a valid measurement set."""
    raise NotImplementedError


@then('the subsystem Tango devices <devices> will change to obsState CONFIGURING')
def the_subsystem_tango_devices_devices_will_change_to_obsstate_configuring():
    """the subsystem Tango devices <devices> will change to obsState CONFIGURING."""
    raise NotImplementedError


@then('the subsystem Tango devices <devices> will change to obsState SCANNING')
def the_subsystem_tango_devices_devices_will_change_to_obsstate_scanning():
    """the subsystem Tango devices <devices> will change to obsState SCANNING."""
    raise NotImplementedError

