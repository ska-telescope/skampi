@VTS-225
Feature: Verification of OET scripts being executed successfully during an observation

	#*Scenario: Starting up telescope*
	@XTP-780 @XTP-776
	Scenario: Starting up telescope
		Given telescope is in STANDBY or OFF state
		When I tell the OET to run startup script file:///scripts/startup.py
		Then the central node goes to state ON


    #*Scenario: Setting telescope to stand-by*
	@XTP-781 @XTP-776
	Scenario: Setting telescope to stand-by
		Given telescope is in ON state
		When I tell the OET to run standby script file:///scripts/standby.py
		Then the central node goes to state STANDBY


	#*Scenario: Starting up low telescope*
	Scenario: Starting up low telescope
		Given low telescope is in STANDBY or OFF state
		When I turn telescope to ON state
		Then the central node goes to state ON