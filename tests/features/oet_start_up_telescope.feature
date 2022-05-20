@VTS-225
Feature: Verification of OET scripts being executed successfully during an observation

	#*Scenario: Starting up mid telescope*
	@XTP-780 @XTP-776
	Scenario: Starting up mid telescope
		Given an OET
		When I tell the OET to run file:///scripts/startup.py
		Then the central node must be ON


    #*Scenario: Setting telescope to stand-by*
	@XTP-781 @XTP-776
	Scenario: Setting telescope to stand-by
		Given an OET
		When I tell the OET to run file:///scripts/standby.py
		Then the central node must be OFF
