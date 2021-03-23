
# coding=utf-8
import pytest
"""Default feature tests."""
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)
@pytest.mark.singlerun
@scenario('XTP-1310.feature', 'PSI0.1 test, Initialise the TPM using the OET (Jupyter Notebook)')
def test_psi01_test_initialise_the_tpm_using_the_oet_jupyter_notebook():
    """PSI0.1 test, Initialise the TPM using the OET (Jupyter Notebook)."""
@given('subsystems <subsystem-list> are ONLINE and in the Tango Device OFF state')
def subsystems_are_online_and_in_the_tango_device_off_state(subsystem_list):
    """subsystems <subsystem-list> are ONLINE and in the Tango Device OFF state."""
    raise NotImplementedError
@given('the TPM_HW is powered ON and in the IDLE state')
def the_tpm_hw_is_powered_on_and_in_the_idle_state():
    """the TPM_HW is powered ON and in the IDLE state."""
    raise NotImplementedError
@given('the Tile Tango Device is ONLINE and in the DISABLE state')
def the_tile_tango_device_is_online_and_in_the_disable_state():
    """the Tile Tango Device is ONLINE and in the DISABLE state."""
    raise NotImplementedError
@when('I send the command <command> to the TMC')
def i_send_the_command_to_the_tmc(command):
    """I send the command <command> to the TMC."""
    raise NotImplementedError
@then('the TPM_HW is in the WORKING state')
def the_tpm_hw_is_in_the_working_state():
    """the TPM_HW is in the WORKING state."""
    raise NotImplementedError
@then('the TPM_HW will be programmed and initialized')
def the_tpm_hw_will_be_programmed_and_initialized():
    """the TPM_HW will be programmed and initialized."""
    raise NotImplementedError
@then('the state and the temperature of the TPM_HW can be monitored.')
def the_state_and_the_temperature_of_the_tpm_hw_can_be_monitored():
    """the state and the temperature of the TPM_HW can be monitored.."""
    raise NotImplementedError
 
