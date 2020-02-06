@XR-13
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

	
	@XTP-417 @XTP-494
	Scenario: A1-Test, Sub-array resource allocation
		Given A running telescope for executing observations on a subarray
		When I allocate 4 dishes to subarray 1
		Then I have a subarray composed of 4 dishes
		And the subarray is in the condition that allows scan configurations to take place
		
			

	
	@XTP-427 @XTP-494
	Scenario: A2-Test, Sub-array transitions from IDLE to READY state
		Given I am accessing the console interface for the OET
		And sub-array is in IDLE state
		When I call the configure scan execution instruction
		Then sub-array is in READY state for which subsequent scan commands can be directed to deliver a basic imaging outcome
			

	
	@XTP-436 @XTP-494
	Scenario: A4-Test, Sub-array deallocation of resources
		Given SKA Mid telescope
		And The telescope is ready
		And A subarray definition
		And A resource allocation definition
		And a means of observing the tmc subarray
		And a means of observing the csp subarray
		And a means of observing the csp master
		And a means of observing the sdp subarray
		And a means of observing the sdp master
		And a monitor on the tmc subarray state
		And a monitor on csp subarray state
		And a monitor on sdp subarray state
		And a way of monitoring receptor ID list
		And I allocate resources to a subarray
		When I deallocate the resources
		Then subarray should go into OFF state
			

	
	@XTP-428 @XTP-494
	Scenario: A3-Test, Sub-array performs an observational imaging scan
		Given I am accessing the console interface for the OET
		And Sub-array is in READY state
		When I call the execution of the scan instruction
		And duration of scan is TBD seconds
		Then Sub-array is in SCANNING state 
		And basic imaging outcome is delivered
		And observation ends after TBD seconds