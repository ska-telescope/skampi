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
		When I tell the OET to allocate resources using script file:///scripts/allocate_from_file_sb.py and SBI /tmp/oda/mid_sb_example.json
		Then the sub-array goes to ObsState IDLE


