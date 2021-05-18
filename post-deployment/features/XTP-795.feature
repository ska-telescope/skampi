@VTS-225
Feature: Verification of OET scripts being executed successfully during an observation

	#Scenario: Allocate resources without a SBI
	@XTP-790 @XTP-795
	Scenario: Allocating resources without a SBI
		Given sub-array is in ObsState EMPTY
		When I tell the OET to allocate resources using script file:///app/scripts/allocate_from_file.py and scripts/data/example_allocate.json
		Then the sub-array goes to ObsState IDLE

	#Scenario: Observing without a SBI
	@XTP-791 @XTP-795
	Scenario: Configuring a subarray and performing scan without a SBI
		Given OET has allocated resources with file:///app/scripts/allocate_from_file.py and scripts/data/example_allocate.json
		When I tell the OET to configure a subarray and perform scan using script file:///app/scripts/observe.py and scripts/data/example_configure.json
		Then the sub-array passes through ObsStates IDLE, CONFIGURING, SCANNING, IDLE

