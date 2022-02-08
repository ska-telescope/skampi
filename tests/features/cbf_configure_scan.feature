@XTP-4603
Feature: Configure scan on CBF subarray

	
	@XTP-4601 @XTP-4600 @XTP-3324
	Scenario: Configure scan on CBF mid subarray
		Given an CBF subarray in IDLE state
		When I configure it for a scan
		Then the CBF subarray must be in the READY state	

	
	@XTP-4602 @XTP-4600 @XTP-3325
	Scenario: Configure scan on CBF low subarray
		Given an CBF subarray in IDLE state
		When I configure it for a scan
		Then the CBF subarray must be in the READY state