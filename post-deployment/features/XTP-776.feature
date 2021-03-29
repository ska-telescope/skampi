@VTS-225
Feature: Verification of OET scripts being executed successfully during an observation

	#*Scenario: Starting up the telescope*
	@XTP-780 @XTP-776
	Scenario: Starting up the telescope
		Given telescope is in OFF State
		When I tell the OET to run file:///app/scripts/startup.py
		Then the central node goes to state ON


    #*Scenario: Setting telescope to stand-by*
	@XTP-781 @XTP-776
	Scenario: Setting telescope to stand-by
		Given telescope is in ON State
		When I tell the OET to run file:///app/scripts/standby.py
		Then the central node goes to state OFF