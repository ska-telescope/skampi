# SP354 configuration and demo script

This folder contains instructions on how to exercise the OET and MVP for the
SP354 demo. 

This folder contains:

<dl>
  <dt>README.md</dt>
  <dd>This file</dd>
  
  <dt>polaris_b1.json</dt>
  <dd>A serialised CDM configuration that configures a subarray to perform a simple Band 1 observation of Polaris</dd>
  
  <dt>scanrunner.py</dt>
  <dd>a script that performs an observation using scan definitions contained in a file</dd>
  
  <dt>scan_definitions.csv</dt>
  <dd>a scan definition file that performs one scan, the observation of Polaris as described above.</dd>
</dl>

## Launching the integrated environment

First, pull the latest images to be sure you're not using anything outdated.

```bash
# pull the images referenced in the docker-compose definitions, including
# the latest builds of anything tagged :latest.
make pull
```

Register the Tango devices and start the integrated environment with

``` bash
# register the MVP devices with the Tango database
make ds-config

# Optional step: import WebJive dashboards
# WARNING! This will overwrite any existing WebJive dashboards!
make import_dashboards

# launch Tango, WebJive, OET and the MVP device containers
make mvp
```

## Example itango session

To connect to the OET interactive itango session, execute

``` bash
docker attach oet
```

Once at the command prompt, execute the following commands

```
# change directory to this folder
cd /host/sp354

# start up the telescope, turning DISH master devices on
telescope = SKAMid()
telescope.start_up()

# Create a sub-array and allocate two dishes to it
subarray = SubArray(1)
allocation = ResourceAllocation(dishes=[Dish(1), Dish(2)])
subarray.allocate(allocation)

# Load and configure a sub-array from a CDM definition file
# This CDM configures for a Band 1 observation of Polaris.
subarray.configure_from_file('polaris_b1.json')

# scan for 10 seconds
subarray.scan(10.0)

# We can't reconfigure a sub-array yet, so mark the end of
# the observation
subarray.end_sb()

# (optional) deallocate all sub-array resources
subarray.deallocate()

# (optional) send the telescope to STANDBY
telescope.standby()
```

Press <kbd>ctrl</kbd>+<kbd>p</kbd> <kbd>ctrl</kbd>+<kbd>q</kbd> to detach
from the itango session.

## scanrunner.py execution

The scanrunner.py script executes a sequence of scans defined in a CSV file. 
The CSV file defines an scan as a CDM configuration to apply and a scan
duration. A multiple scan observation can be defined by defining multiple
scan definitions, one definition per rows.

The script assumes a state where the telescope is started and resources have
been assigned to sub-array #1. The script then performs a sequence of scans
and ends the SB, before returning control to the command prompt.

Note: the MVP devices cannot perform more than one scan, so you may need to
restart the system if you have already performed a scan.

``` bash
# Do a full system restart to get around the MVP 'one scan' device limitations
make down
make mvp

# Reconnect to the OET itango session
docker attach oet
```

Once at the itango command prompt, start the telescope and prepare a sub-array
with

```
# start up the telescope, turning DISH master devices on
telescope = SKAMid()
telescope.start_up()

# Create a sub-array and allocate two dishes to it
subarray = SubArray(1)
allocation = ResourceAllocation(dishes=[Dish(1), Dish(2)])
subarray.allocate(allocation)
```

Now execute the scanrunner script, providing the configuration file to execute as
an argument to the script.

```
# change directory to this folder
cd /host/sp354

# Use %run ipython magic to execute the script
%run scanrunner.py scan_configurations.csv
```
