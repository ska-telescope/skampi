Feature: Test Configure functionality with the subarray using TMC with invalid input
	@XTP-14719
	Scenario: Configure the mid telescope subarray using TMC with invaid input
		Given an TMC
		Given an telescope subarray
		I assign resources to the subarray
		When I configure it for a scan with invalid input
		Then the subarray rejects the command and remain in IDLE obsstate

	@XTP-16185
	Scenario: Configure the low telescope subarray using TMC with invalid input
		Given an TMC
		Given an telescope subarray
		I assign resources to the subarray
		When I configure it for a scan with invalid input
		Then the subarray rejects the command and remain in IDLE obsstate
