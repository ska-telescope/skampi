@XTP-522
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
​
	
	@XTP-417 @XTP-494
	Scenario: A1 Test, Sub-array resource allocation
		Given A running telescope for executing observations on a subarray
		When I allocate 4 dishes to subarray 1
		Then I have a subarray composed of 4 dishes
		And the subarray is in the condition that allows scan configurations to take place
		