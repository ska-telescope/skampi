@XTP-6189
Feature: Assign resources to subarray using TMC


	@XTP-6188 @XTP-6186 @XTP-3324
	Scenario: Assign resources to mid subarray
		Given an TMC
		Given an telescope subarray
		When I assign resources to it
		Then the subarray must be in IDLE state

	@XTP-9002 @XTP-6186 @XTP-3324
	Scenario: Release resources from mid subarray
		Given an TMC
		Given an telescope subarray
		Given a subarray in the IDLE state
		When I release all resources assigned to it
		Then the subarray must be in EMPTY state

	Scenario: Assign resources to low subarray
		Given an TMC
		Given an telescope subarray
		When I assign resources to it
		Then the subarray must be in IDLE state

	Scenario: Release resources from low subarray
		Given an TMC
		Given an telescope subarray
		Given a subarray in the IDLE state
		When I release all resources assigned to it
		Then the subarray must be in EMPTY state
