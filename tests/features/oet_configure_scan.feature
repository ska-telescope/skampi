Feature: Configure the subarray using OET

    Scenario: Configure the low telescope subarray using OET
		Given an OET
		Given a low telescope subarray in IDLE state
		When I configure it for a scan
		Then the subarray must be in the READY state