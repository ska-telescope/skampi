Feature: Configure scan on telescope subarray

	Scenario: Configure scan on telescope subarray in mid
		Given a telescope subarray in IDLE state
		When I configure it for a scan
		Then the subarray must be in the READY state