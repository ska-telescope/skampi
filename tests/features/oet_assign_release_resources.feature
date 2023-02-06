@VTS-225
Feature: Verification of OET scripts being executed successfully during an observation

	@XTP-779 @XTP-776
	Scenario: Creating a new SBI with updated SB IDs and PB IDs
		Given an OET
		When I tell the OET to create SBI using script file:///scripts/create_sbi.py and SB /tmp/oda/mid_sb_example.json
		Then the script completes successfully

	#Scenario: Allocate resources with a SBI
	@XTP-777 @XTP-776
	Scenario: Allocating resources with a SBI
		Given an OET
		And  sub-array is in ObsState EMPTY
		When I tell the OET to allocate resources using script file:///scripts/allocate_from_file_mid_sb.py and SBI /tmp/oda/mid_sb_example.json
		Then the sub-array goes to ObsState IDLE

	#Scenario: Release all resources
	@XTP-782 @XTP-776
	Scenario: Releasing all resources from sub-array
		Given sub-array with resources allocated to it
		When I tell the OET to release resources using script file:///scripts/deallocate.py
		Then the sub-array goes to ObsState EMPTY

	#Scenario: Allocate resources using oet scripting interface
	@XTP-777 @XTP-776
	Scenario: Allocate resources using oet scripting interface
		Given an OET
		And an oet subarray object in state EMPTY
		When I assign resources to it
		Then the sub-array goes to ObsState IDLE

	#Scenario: Allocate resources using oet scripting interface low
	Scenario: Allocate resources using oet scripting interface low
		Given an OET
		And an oet subarray object in state EMPTY
		When I assign resources to it in low
		Then the sub-array goes to ObsState IDLE

	#Scenario: Release all resources low
	Scenario: Release all resources from sub-array low
		Given sub-array with resources allocated to it
		When I tell the OET to release resources
		Then the sub-array goes to ObsState EMPTY
