@XTP-4780
Feature: Run a Scan on CSP Subarray

	
	@XTP-4771 @XTP-4769 @XTP-4679 @XTP-4676 @XTP-3324
	Scenario: Run a scan on CSP mid subarray
		Given an CSP subarray in READY state
		When I command it to scan for a given period
		Then the CSP subarray must be in the SCANNING state until finished	

	
	@XTP-4772 @XTP-4769 @XTP-4680 @XTP-4676 @XTP-3325
	Scenario: Run a scan on CSP low subarray
		Given an CSP subarray in READY state
		When I command it to scan for a given period
		Then the CSP subarray must be in the SCANNING state until finished