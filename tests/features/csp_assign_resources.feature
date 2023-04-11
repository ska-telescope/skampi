@XTP-4634
Feature: Assign resources to CSP subarray

	
	@XTP-4636 @XTP-5537 @XTP-4635 @XTP-3324 @XTP-5573
	Scenario: Assign resources to CSP mid subarray
		Given an CSP subarray
		When I assign resources to it
		Then the CSP subarray must be in IDLE state	

	
	@XTP-4637 @XTP-5537 @XTP-4635 @XTP-3325 @XTP-5539
	Scenario: Assign resources to CSP low subarray
		Given an CSP subarray
		When I assign resources to it
		Then the CSP subarray must be in IDLE state

	@XTP-5538 @XTP-5537 @XTP-4635 @XTP-3325 @XTP-5539
	Scenario: Release resources assigned to an CSP low subarray
		Given an CSP subarray in IDLE state
		When I release all resources assigned to it
		Then the CSP subarray must be in EMPTY state

	@XTP-5787 @XTP-5537 @XTP-4635 @XTP-3324
	Scenario: Release resources assigned to an CSP mid subarray
		Given an CSP subarray in IDLE state
		When I release all resources assigned to it
		Then the CSP subarray must be in EMPTY state

	@XTP-16154
	Scenario: Assign resources with invalid config to CSP
		Given an CSP subarray
		When I assign resources with invalid config
		Then the subarray should throw an exception and remain in the previous state
	@XTP-20082 @XTP-5537 @XTP-4635 @XTP-3324
	Scenario: Abort assigning CSP
		Given an subarray busy assigning
		When I command it to Abort
		Then the subarray should go into an aborted state
