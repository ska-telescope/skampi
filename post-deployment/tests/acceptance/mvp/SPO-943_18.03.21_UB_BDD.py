#!/usr/bin/env python
# coding: utf-8

# # SPO-943_UB edited (17 March 2021)

# First, import essential Python libraries used by this notebook.

# In[1]:


import time  # used to sleep between measurements


# Create DeviceProxies to the remote TMC and MCCS Tango devices we want to
# control and monitor in this session.

# In[2]:


# create device proxy to TMC CentralNode
tmc_central_node = DeviceProxy('ska_low/tm_central/central_node')

# create device proxy to MCCS controller, station, and tile
mccs_controller = DeviceProxy('low-mccs/control/control')
mccs_station_001 = DeviceProxy('low-mccs/station/001')
mccs_tile_0001 = DeviceProxy('low-mccs/tile/0001')


# Create some convenience variables and functions to make subsequent code easier
# to read.

# In[3]:


# Create a shortcut for ON and OFF states
ON = tango._tango.DevState.ON
OFF = tango._tango.DevState.OFF

# Create a list holding the target devices in the control chain
ALL_DEVICES = [
    tmc_central_node,
    mccs_controller,
    mccs_station_001,
    mccs_tile_0001
]

# Define a function to print the state of all devices
def print_device_states():
    for device in ALL_DEVICES:
        device_name = str(device).split('(')[0]
        device_state = device.State()
        print(f'{device_name}: {device_state}')


# As we haven't run any commands, the initial status of the telescope should be
# OFF.

# Given subsystems <subsystem-list> are ONLINE (with Tango Device in OFF state,except MccsTile in the DISABLE or OFF state)
def given_online():

    for device in ALL_DEVICES:
        assert device.State() is OFF, f'{device} is not in OFF state'

    print_device_states()


# And the TPM_HW is powered ON and in the IDLE state (pass)
def tpm_on():
    pass

# ### Turning on the telescope confirming state changes

# First, start up the telescope executing the cell below. Start up the telescope
# by calling the 'startuptelescope' command on the TMC Central Node. This
# instructs TMC to power up or initialise all the devices under its control.
# 
# As of PI9, turning on a telescope that is already on causes an irrecoverable
# failure. So, the code below confirms that the system is not already in state
# 'ON' before issuing the command.

# When I send the command <command> to the TMC
def tmc_command_on():
    
    if tmc_central_node.State() is not ON:
        print('Control system is off. Starting up telescope...')
        tmc_central_node.startuptelescope()
        time.sleep(20)
    else:
        print('Control system is already on. No start up command issued.')


# The status of the telescope, station, and tile should now have changed from
# OFF to ON.

# Then the TPM_HW will be programmed and initialized

# And the TPM_HW is in the WORKING state

# In[7]:


for device in [tmc_central_node, mccs_controller, mccs_tile_0001]:
    assert device.State() is ON, f'{device} is not in ON state'


# In[8]:


print_device_states()


# # (SKIP this section) Taking the MCCS Tile out of simulation mode 

# As of PI9 the MCCS tiles are in simulation mode by default. Switching to
# hardware mode if necessary. Simulation mode = 1 and hardware mode = 0

# In[9]:


if mccs_tile_0001.simulationmode == 1:
    print('MCCS tile 0001 is in simulation mode. Switching to hardware mode...')
    mccs_tile_0001.simulationmode = 0
    mccs_tile_0001.command_inout_asynch("Initialise")
    time.sleep(20)
else:
    print('MCCS tile 0001 is already in hardware mode. No command issued.')


# # (Continue here...) Keeping the MCCS Tile in simulation mode

# And the state and the temperature of the TPM_HW can be monitored

# In[9]:


if mccs_tile_0001.simulationmode == 1:
    print ('MCCS tile 0001 is in simulation mode')


# In[11]:


print_device_states()


# First attempt at writing a test to poll the temperature and time of a tile. The cell
# below collates the temperature and time readings of the mccs tile every second
# for twenty seconds. If there is no variation in the temperatures it retrieves, it
# returns an error. This code is a quick and dirty prototype and is not the final
# test.

# In[12]:


device = mccs_tile_0001

measurement_cadence = 1.0  # seconds to wait between measurements
num_measurements_required = 20  # Code will loop until this many measurements are taken

temperature = []
mccs_time = []
while len(temperature) < num_measurements_required:
    temperature.append(device.fpga1_temperature)
    mccs_time.append(device.fpga1_time)
    time.sleep(measurement_cadence)

num_secs = measurement_cadence * num_measurements_required
assert (len(set(temperature))!=1), f"No variation seen in the temperature values of {device} over {num_secs} seconds"
assert (len(set(mccs_time))!=1), f"No variation seen in the time values of {device} over {num_secs} seconds"


# In[13]:


print(temperature)
print(mccs_time)


# Run this cell to put the telescope to standby

# ## Teardown

# In[14]:


tmc_central_node.standbytelescope()


# In[15]:


print_device_states()


# ### End of test

# Run this cell to get the list of attributes you can query

# In[16]:


mccs_tile_0001.get_attribute_list()


# # Don't use the following commands now. These are just examples to change from simulation mode to hardware mode

# In[18]:


mccs_tile_0001.simulationmode = 0


# In[40]:


mccs_tile_0001.simulationmode = 1


# In[10]:


if mccs_tile_0001.simulationmode == 0:
    print ('MCCS tile 0001 is in hardware mode')

