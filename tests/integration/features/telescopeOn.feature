Feature: Default

	
	@XTP-4921
	Scenario: Test TelescopeOn command
		Given TMC and SDP devices are deployed
		And Telescope is in OFF state
		When the operator invokes TelescopeOn command on TMC
		Then the SDP Master turns on and changes its state to ON
