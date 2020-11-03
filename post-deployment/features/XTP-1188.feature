	#@pytest.mark.skip(reason="no way of currently testing this")
	Scenario: A1-Test, Sub-array resource allocation
		Given A running telescope for executing observations on a subarray
		When I allocate 4 dishes to subarray 1
		Then the subarray is in the condition that allows scan configurations to take place

	
   #@pytest.mark.skip(reason="no way of currently testing this")
	Scenario: A2-Test, Sub-array transitions from IDLE to READY state
		Given I am accessing the console interface for the OET
		And sub-array is in IDLE state
		When I call the configure scan execution instruction
		Then sub-array is in READY state for which subsequent scan commands can be directed to deliver a basic imaging outcome
			

	#@pytest.mark.skip(reason="no way of currently testing this")
	Scenario: A3-Test, Sub-array performs an observational scan
	    Given Sub-array is in ON state
		And Sub-array is configured successfully
		And Fixture returns Scan input JSON string
		When I call the execution of the scan command for duration of 10 seconds
		Then Sub-array changes to a SCANNING state
		And observation ends after 10 seconds as indicated by returning to READY state