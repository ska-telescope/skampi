@XTP-522
@XR-13
Feature: Demonstrate the Subarray Basic State Machine (MVP PI5)
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

	#+This was the first version of Acceptance Criteria 1:+
	#
	#Given I am accessing the console interface for the OET
	#And there is an available sub-array in OFFLINE state
	#When I call the resource assignment instruction
	#And assign 4 dish receptors
	#And set up CSP resources for signal processing
	#And set up SDP resources for processing signals from 4 receptors
	#Then sub-array is in IDLE state for which subsequent configuration and scan commands can be directed to the sub-array as a whole
	@XTP-417 @XTP-494
	Scenario: A1 Test: Sub-array transitions from OFFLINE to IDLE state
		Given A running telescope for executing observations on a subarray
		When I allocate 4 dishes to subarray 1
		Then I have a subarray composed of 4 dishes
		And the subarray is in a state READY for executing observations by means of scheduling blocks
		
		