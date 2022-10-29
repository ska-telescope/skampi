@XTP-9991
Feature: Configure the CSP for a scan using csp leaf node
	@XTP-9992 @XTP-9993 @XTP-9994
	Scenario: Configure the csp mid using csp leaf node
		Given a CSP
		Given a CSP leaf node
		When I configure it for a scan
		Then the csp subarray must be in READY state