Feature: Configure scan on telescope subarray

	Scenario: Configure scan on telescope subarray in mid
		Given an TMC
		Given an telescope subarray
		Given a subarray in the IDLE state
		When I configure it for a scan
		Then the subarray must be in the READY state