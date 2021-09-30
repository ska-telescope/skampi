@VTS-225
Feature: Verification of OET scripts being executed successfully during an observation
	#ALL below scenarios are specific for the SKA-LOW
	#*Scenario: Starting up the telescope*
	@XTP-2414 @XTP-2413
	Scenario: Starting up telescope
		Given telescope is in OFF State
		When I tell the OET to run file:///app/scripts/startup.py
		Then the central node goes to state ON

	#Scenario: Creating a new SBI
	@XTP-2415 @XTP-2413
	Scenario: Creating a new SBI with updated SB IDs and PB IDs
		Given the SKUID service is running
		When I tell the OET to create SBI using script file:///app/scripts/create_sbi.py and SB scripts/data/example_low_sb.json
		Then the script completes successfully

	#Scenario: Allocate resources with a SBI
	@XTP-2416 @XTP-2413
	Scenario: Allocating resources with a SBI
		Given sub-array is in ObsState EMPTY
		And the OET has used file:///app/scripts/create_sbi.py to create SBI scripts/data/example_low_sb.json
		When I tell the OET to allocate resources using script file:///app/scripts/low_allocate_from_file_sb.py and SBI scripts/data/example_low_sb.json
		Then the sub-array goes to ObsState IDLE

	#Scenario: Observing a SBI
	@XTP-2417 @XTP-2413
	Scenario: Observing a Scheduling Block
		Given the OET has used file:///app/scripts/create_sbi.py to create SBI scripts/data/example_low_sb.json
		And OET has allocated resources with file:///app/scripts/low_allocate_from_file_sb.py and scripts/data/example_low_sb.json
		When I tell the OET to observe SBI scripts/data/example_low_sb.json using script file:///app/scripts/low_observe_sb.py
		Then the sub-array passes through ObsStates IDLE, CONFIGURING, SCANNING, CONFIGURING, SCANNING, CONFIGURING, SCANNING, CONFIGURING, SCANNING, IDLE

	#*Scenario: Releasing resources of sub-array*
	@XTP-2418 @XTP-2413
	Scenario: Release resources
		Given the sub-array is in ObsState IDLE
		When I tell the OET to release resources by running file:///app/scripts/deallocate.py
		Then the sub-array goes to ObsState EMPTY

	#*Scenario: Setting telescope to stand-by*
	@XTP-2419 @XTP-2413
	Scenario: Setting telescope to stand-by
		Given telescope is in ON State
		When I tell the OET to run file:///app/scripts/standby.py
		Then the central node goes to state OFF