@XTP-13146
Scenario: Scan the csp mid using csp leaf node
	Given a CSP subarray in the READY state
	Given a TMC CSP subarray Leaf Node
	When I command it to scan for a given period
	Then the CSP subarray shall go from READY to SCANNING
	Then the CSP shall go back to READY when finished

@XTP-16189
Scenario: Scan the csp low using csp leaf node
    Given a CSP subarray in the READY state
    Given a TMC CSP subarray Leaf Node
    When I command it to scan for a given period
    Then the CSP subarray shall go from READY to SCANNING
    Then the CSP shall go back to READY when finished
