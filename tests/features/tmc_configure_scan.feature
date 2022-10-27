Feature: Configure the subarray using TMC

	Scenario: Configure the mid telescope subarray using TMC
		Given an TMC
		Given an telescope subarray
		Given a subarray in the IDLE state
		When I configure it for a scan
		Then the subarray must be in the READY state