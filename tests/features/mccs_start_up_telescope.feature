@XTP-3984
Feature: Start up the MCCS

	
	@XTP-3982 @XTP-3983 @XTP-3325
	Scenario: Start up the MCCS
		Given the MCCS
		When I start up the telescope
		Then the MCCS must be on	