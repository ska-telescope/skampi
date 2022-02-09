@XTP-4638
Feature: Configure scan on CSP subarray

	
	@XTP-4640 @XTP-4639 @XTP-3324
	Scenario: Configure scan on CSP mid subarray
		Given an CSP subarray in IDLE state
		When I configure it for a scan
		Then the CSP subarray must be in the READY state	

	
	@XTP-4641 @XTP-4639 @XTP-3325
	Scenario: Configure scan on CSP low subarray
		Given an CSP subarray in IDLE state
		When I configure it for a scan
		Then the CSP subarray must be in the READY state