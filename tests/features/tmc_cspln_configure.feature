@XTP-XXXX
Feature: Configure the CSP for a scan using csp leaf node
	# @XTP-XXXX @XTP-XXXX @XTP-XXXX
	Scenario: Configure the csp mid using csp leaf node
		Given a CSP
		Given a CSP leaf node
		When I configure it for a scan
		Then the csp subarray must be in READY state