Feature: Default

	
	@XTP-3514
	Scenario: Tangojql service available
		Given a configuration to access a tango device remotely
		When I send a ping command to the tango database device server
		Then I expect a response to be returned from the device server