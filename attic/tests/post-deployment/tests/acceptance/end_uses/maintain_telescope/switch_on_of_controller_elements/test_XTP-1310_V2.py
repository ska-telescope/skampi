# coding=utf-8
import pytest
"""Default feature tests."""
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)
import logging
import time  # used to sleep between measurements
from ska_ser_skallop.transactions.atomic import atomic
from ska_ser_skallop.connectors.configuration import get_device_proxy


logger = logging.getLogger(__name__)

class DeviceStates:
    
    def __init__(self):
        # create device proxy to TMC CentralNode
        self.tmc_central_node = get_device_proxy('ska_low/tm_central/central_node')

        # create device proxy to MCCS controller, station, and tile
        self.mccs_controller = get_device_proxy('low-mccs/control/control')
        self.mccs_station_001 = get_device_proxy('low-mccs/station/001')
        self.mccs_tile_0001 = get_device_proxy('low-mccs/tile/0001')
        # Create a list holding the target devices in the control chain
        self.ALL_DEVICES = [
            self.tmc_central_node,
            self.mccs_controller,
            self.mccs_station_001,
            self.mccs_tile_0001
        ]

        self.all_device_names = [device.name() for device in self.ALL_DEVICES]

    def print_device_states(self):
        for device in self.ALL_DEVICES:
            device_name = str(device).split('(')[0]
            device_state = device.State()
            logger.info(f'{device_name}: {device_state}')


@pytest.fixture
def devices()-> DeviceStates:


    return DeviceStates()


# Define a function to print the state of all devices
#@pytest.mark.skip(reason="disabled to check pipeline failure")
@pytest.mark.skalow
@pytest.mark.quarantine
@scenario('XTP-1310.feature', 'PSI0.1 test, Initialise the TPM using the OET (Jupyter Notebook)')
def test_psi01_test_initialise_the_tpm_using_the_oet_jupyter_notebook():
    """PSI0.1 test, Initialise the TPM using the OET (Jupyter Notebook)."""
@given('subsystems are ONLINE (with Tango Device in OFF state,except MccsTile in the DISABLE or OFF state)')
def subsystems_are_online_and_in_the_tango_device_off_state(devices):
    """subsystems <subsystem-list> are ONLINE and in the Tango Device OFF state."""
       
    assert devices.tmc_central_node.State().name == 'OFF', f'tmc_central_node is not in OFF state'
    assert devices.mccs_controller.State().name == 'OFF', f'mccs_controller is not in OFF state'
    assert devices.mccs_station_001.State().name == 'OFF', f'mccs_station_001 is not in OFF state'
    assert devices.mccs_tile_0001.State().name in ['OFF','DISABLE'], f'mccs_tile_0001 is not in OFF or DISABLE state'
    devices.print_device_states()

@given('the TPM_HW is powered ON and in the IDLE state')
def the_tpm_hw_is_powered_on_and_in_the_idle_state():
    """the TPM_HW is powered ON and in the IDLE state."""

@when('I send the command ON to the TMC')
def i_send_the_command_to_the_tmc(devices):
    """I send the command to the TMC."""
 
    if devices.tmc_central_node.State().name != 'ON':
        logger.info('Control system is off. Starting up telescope...')
        with atomic(devices.all_device_names,'state','ON',5):
            devices.tmc_central_node.StartUpTelescope()
            #time.sleep(20)
    else:
        logger.info('Control system is already on. No start up command issued.')

@then('the TPM_HW will be programmed and initialized')
def the_tpm_hw_will_be_programmed_and_initialized(devices):
    """the TPM_HW will be programmed and initialized."""
    for device in [devices.tmc_central_node, devices.mccs_controller, devices.mccs_tile_0001]:
        assert device.State().name == 'ON', f'{device} is not in ON state'

@then("the TPM_HW is in the WORKING state")
def tpm_hardware_working_state():
    # TODO determine how to verify TPM is in WORKING state)
    pass

@then('the state and the temperature of the TPM_HW can be monitored')
def the_state_and_the_temperature_of_the_tpm_hw_can_be_monitored(devices):
    """the state and the temperature of the TPM_HW can be monitored.."""
    if devices.mccs_tile_0001.simulationMode == 1:
        logger.info('MCCS tile 0001 is in simulation mode')
    devices.print_device_states()

    device = devices.mccs_tile_0001

    measurement_cadence = 1.0  # seconds to wait between measurements
    num_measurements_required = 20  # Code will loop until this many measurements are taken
    temperature = []
    mccs_time = []
    while len(temperature) < num_measurements_required:
        temperature.append(device.fpga1_temperature)
        mccs_time.append(device.fpga1_time)
        time.sleep(measurement_cadence)

    # num_secs = measurement_cadence * num_measurements_required
    # assert (len(set(temperature))!=1), f"No variation seen in the temperature values of {device} over {num_secs} seconds"
    # assert (len(set(mccs_time))!=1), f"No variation seen in the time values of {device} over {num_secs} seconds"

    logger.info(temperature)
    logger.info(mccs_time)
    with atomic(devices.all_device_names,'State','OFF',5):
        devices.tmc_central_node.StandByTelescope()
