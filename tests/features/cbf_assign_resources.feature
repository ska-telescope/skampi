@XTP-4599
Feature: Assign resources to CBF subarray

	
	@XTP-4597 @XTP-4596 @XTP-3324 @XTP-5590
	Scenario: Assign resources to CBF mid subarray
		Given an CBF subarray
		When I assign resources to it
		Then the CBF subarray must be in IDLE state	

	
	@XTP-4598 @XTP-4596 @XTP-3325 @XTP-5589
	Scenario: Assign resources to CBF low subarray
		Given an CBF subarray
		When I assign resources to it
		Then the CBF subarray must be in IDLE state