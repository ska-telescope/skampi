Feature: Sacn the subarray using TMC
	@XTP-14719
	Scenario: Scan the mid telescope subarray using TMC
		Given an TMC
		Given an telescope subarray
		Given a subarray in the SCANNING state
		When I provide end scan command
		Then the subarray must be in the READY state