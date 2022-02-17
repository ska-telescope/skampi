@XTP-4781
Feature: Run a scan on CBF subarray

	
	@XTP-4767 @XTP-4764 @XTP-4679 @XTP-4676 @XTP-4779 @XTP-3324
	Scenario: Run a scan on CBF mid subarray
		Given an CBF subarray in READY state
		When I command it to scan for a given period
		Then the CBF subarray must be in the SCANNING state until finished	

	
	@XTP-4768 @XTP-4764 @XTP-4680 @XTP-4676 @XTP-3325
	Scenario: Run a scan on CBF low subarray
		Given an CBF subarray in READY state
		When I command it to scan for a given period
		Then the CBF subarray must be in the SCANNING state until finished