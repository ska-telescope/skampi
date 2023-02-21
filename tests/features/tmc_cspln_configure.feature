@XTP-13145
Scenario: Configure the csp mid using csp leaf node
	Given a CSP subarray in the IDLE state
	Given a TMC CSP subarray Leaf Node
	When I configure it for a scan
	Then the CSP subarray shall go from IDLE to READY state

@XTP-16187
Scenario: Configure the csp low using csp leaf node
	Given a CSP subarray in the IDLE state
	Given a TMC CSP subarray Leaf Node
	When I configure it for a scan
	Then the CSP subarray shall go from IDLE to READY state

