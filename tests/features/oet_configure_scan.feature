Scenario: Configure the low telescope subarray using OET
		Given an OET
		Given a low telescope subarray in IDLE state
		Given a valid scan configuration
		When I configure it for a scan
		Then the subarray must be in the READY state
        