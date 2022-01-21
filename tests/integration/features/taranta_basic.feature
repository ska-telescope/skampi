@XTP-3768
Feature: Taranta Basic services working

	
	@XTP-3514 @XTP-3767 @XTP-3348 @taranta
	Scenario: TangoGQL service available
		Given a configuration to access a tango device remotely
		When I send a ping command to the tango database device server
		Then I expect a response to be returned from the device server	

	
	@XTP-3771 @XTP-3767 @XTP-3348 @taranta
	Scenario: taranta devices service available
		Given a deployed Taranta web devices service
		When I call its REST url
		Then I get a valid response	

	
	@XTP-3773 @XTP-3767 @XTP-3348 @taranta
	Scenario: taranta dashboard services available
		Given a deployed Taranta web dashboard service
		When I call its REST url
		Then I get a valid response