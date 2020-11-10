	#@pytest.mark.skip(reason="no way of currently testing this")
	@skalow
	Scenario: TMC and MCCS subarray resource allocation
		Given A running telescope for executing observations on a subarray
		When I allocate resources to TMC and MCCS Subarray
		Then The TMC and MCCS subarray is in the condition that allows scan configurations to take place

	
   #@pytest.mark.skip(reason="no way of currently testing this")
   @skalow
	Scenario: TMC and MCCS subarray transitions from IDLE to READY state
		Given A running telescope for executing observations on a subarray
		And Subarray is in IDLE state
		When I call the configure scan execution instruction
		Then Subarray is in READY state for which subsequent scan commands can be directed to deliver a basic imaging outcome
			

	#@pytest.mark.skip(reason="no way of currently testing this")
	@skalow
	Scenario: TMC and MCCS subarray performs an observational scan
	    Given Subarray is in ON state
		And Subarray is configured successfully
		When I call the execution of the scan command for duration of 10 seconds
		Then Subarray changes to a SCANNING state
		And Observation ends after 10 seconds as indicated by returning to READY state