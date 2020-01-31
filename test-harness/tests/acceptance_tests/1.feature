Feature: 

	
	@XTP-277 @XTP-276
	Scenario: Test Tango setup
		Given A set of tango devices
		
		When I check the number of active devices
		
		Then The number of active devices should be more than 50	

	
	@XTP-293 @XTP-276
	Scenario: Telescope startup
		Given a telescope configuration file and a running webjive instance
		
		When the configuration file is passed to webjive
		
		Then the telescope is configured


	@AT1-444 @AT1-444
    Scenario: Assign Resources
		Given I have a OET commands

		When start up the telescope, turning DISH master devices on

		And I call assignResources

		Then subarray states changes to ON
