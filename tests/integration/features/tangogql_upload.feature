@XTP-3768
Feature: Tango GQL service available

	
	@XTP-3514 @XTP-3767 @XTP-3348
	Scenario: TangoGQL service available
		Given a configuration to access a tango device remotely
		When I send a ping command to the tango database device server
		Then I expect a response to be returned from the device server