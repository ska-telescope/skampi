Scenario: Configure the low telescope subarray using OET
		Given an OET
		Given a valid scan configuration
		When I configure it for a scan
		Then the subarray must be in the READY state
        