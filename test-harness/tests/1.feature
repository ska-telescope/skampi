Feature: 

	
	@XTP-277 @XTP-276
	Scenario: Test Tango setup
		Given A set of tango devices
		
		When I check the number of active devices
		
		Then The number of active devices should be more than 50
