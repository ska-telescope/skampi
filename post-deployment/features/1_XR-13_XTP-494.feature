@VTS-221
Feature: Execute a basic observation for the MVP PI5 subarray
	#Demonstrate the sub-array ([Fig 1|https://confluence.skatelescope.org/display/SE/Understanding+Sub+array+state]) according to the following state machine ([Fig 3|https://confluence.skatelescope.org/display/SE/Understanding+Sub+array+state]) for a imaging scan.  
	#  
	#  
	#  
	#  
	#  
	#  
	#  
	#  
	#  
	#  
	#  
	# 


	@pytest.mark.xfail
	@XTP-417 @XTP-494
	Scenario: A1-Test, Sub-array resource allocation
		Given A running telescope for executing observations on a subarray
		When I allocate 4 dishes to subarray 1
		Then I have a subarray composed of 4 dishes
		And the subarray is in the condition that allows scan configurations to take place


	
    @pytest.mark.xfail
	@XTP-427 @XTP-494
	Scenario: A2-Test, Sub-array transitions from IDLE to READY state
		Given I am accessing the console interface for the OET
		And sub-array is in IDLE state
		When I call the configure scan execution instruction
		Then sub-array is in READY state for which subsequent scan commands can be directed to deliver a basic imaging outcome
			

	@pytest.mark.xfail
	@XTP-436 @XTP-494
	Scenario: A4-Test, Sub-array deallocation of resources
		Given A running telescope with "4" dishes are allocated to "subarray 1"
		When I deallocate the resources
		Then "subarray 1" should go into OFF state
		And ReceptorList for "subarray 1" should be empty


@pytest.mark.xfail
	@XTP-428 @XTP-494
	Scenario: A3-Test, Sub-array performs an observational imaging scan
	    Given I am accessing the console interface for the OET
		And Sub-array is in READY state
		And duration of scan is 10 seconds
		When I call the execution of the scan instruction
		Then Sub-array changes to a SCANNING state
		And observation ends after 10 seconds as indicated by returning to READY state
