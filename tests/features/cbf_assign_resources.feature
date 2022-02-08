Feature: Assign resources to CBF subarray

	Scenario: Assign resources to CBF mid subarray
		Given an CBF subarray
		When I assign resources to it
		Then the CBF subarray must be in IDLE state	

	
	Scenario: Assign resources to CBF low subarray
		Given an CBF subarray
		When I assign resources to it
		Then the CBF subarray must be in IDLE state