Feature: Configure the subarray using TMC
	@XTP-14719
	Scenario: Configure the mid telescope subarray using TMC
		Given an TMC
		Given an telescope subarray
		Given a subarray in the IDLE state
		When I configure it for a scan
		Then the subarray must be in the READY state

	@XTP-16155
	Scenario: Configure invalid scan on subarray using TMC
		Given an TMC
		Given an telescope subarray
		Given a subarray in the IDLE state
		When I configure it for a scan with an invalid configuration
		Then the subarray should throw an exception and remain in the previous state