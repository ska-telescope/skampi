Feature: Assign resources to CSP subarray


	Scenario: Assign resources to CSP mid subarray
		Given an CSP subarray
		When I assign resources to it
		Then the CSP subarray must be in IDLE state	


	Scenario: Assign resources to CSP low subarray
		Given an CSP subarray
		When I assign resources to it
		Then the CSP subarray must be in IDLE state