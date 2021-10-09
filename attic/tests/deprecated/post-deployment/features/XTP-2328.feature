@VTS-225
Feature: Verification of OET scripts being executed successfully during an observation

	#Scenario: Allocate resources without a SBI
	@XTP-2325 @XTP-2328
	Scenario: Allocating resources without an SBI
		Given sub-array is in ObsState EMPTY
		When I tell the OET to allocate resources using script file:///app/scripts/allocate_from_file.py and scripts/data/example_allocate.json
		Then the sub-array goes to ObsState IDLE

	#Scenario: Observing without a SBI
	@XTP-2330 @XTP-2328
	Scenario: Configuring a subarray and performing scan without an SBI
		Given A running telescope with 2 dishes are allocated to sub-array for executing observations
		When I tell the OET to configure a sub-array and perform scan for duration 10.0 sec using script file:///app/scripts/observe.py and scripts/data/example_configure.json
		Then the sub-array passes through ObsStates IDLE, CONFIGURING, SCANNING, IDLE

