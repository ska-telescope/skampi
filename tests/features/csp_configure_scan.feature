Feature: Configure scan on CSP subarray


	Scenario: Configure scan on CSP mid subarray
		Given an CSP subarray in IDLE state
		When I configure it for a scan
		Then the CSP subarray must be in the READY state	

	
	Scenario: Configure scan on CSP low subarray
		Given an CSP subarray in IDLE state
		When I configure it for a scan
		Then the CSP subarray must be in the READY state