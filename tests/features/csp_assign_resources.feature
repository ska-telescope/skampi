@XTP-4634
Feature: Assign resources to CSP subarray

	
	@XTP-4636 @XTP-4635 @XTP-3324
	Scenario: Assign resources to CSP mid subarray
		Given an CSP subarray
		When I assign resources to it
		Then the CSP subarray must be in IDLE state	

	
	@XTP-4637 @XTP-4635 @XTP-3325
	Scenario: Assign resources to CSP low subarray
		Given an CSP subarray
		When I assign resources to it
		Then the CSP subarray must be in IDLE state

	Scenario: Release resources assigned to an CSP low subarray
		Given an CSP subarray in IDLE state
		When I release all resources assigned to it
		Then the CSP subarray must be in EMPTY state