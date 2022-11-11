@VTS-225
Feature: Verification of OET scripts being executed successfully during an observation

    #Scenario: Observing a SBI
	@XTP-778 @XTP-776
	Scenario: Observing a Scheduling Block
		Given Subarray is in the ObsState IDLE
		When I tell the OET to observe using script "<script>" and SBI "<sb_json>"
		Then the Subarray goes to ObsState READY

    Examples:
    |script                             |sb_json                     |
    |file:///scripts/observe_mid_sb.py  |/tmp/oda/mid_sb_example.json|

