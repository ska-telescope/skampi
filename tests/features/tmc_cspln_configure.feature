@XTP-13145
Scenario: Configure the csp mid using csp leaf node
	Given a TMC CSP subarray Leaf Node
	Given a CSP subarray in the IDLE state
	When I configure it for a scan
	Then the CSP subarray shall go from IDLE to READY state