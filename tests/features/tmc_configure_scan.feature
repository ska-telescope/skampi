Feature: Configure the subarray using TMC
	@XTP-14719
	Scenario: Configure the mid telescope subarray using TMC
		Given an TMC
		Given an telescope subarray
		Given a subarray in the IDLE state
		When I configure it for a scan
		Then the subarray must be in the READY state

	@XTP-16185
	Scenario: Configure the low telescope subarray using TMC
		Given an TMC
		Given an telescope subarray
		Given a subarray in the IDLE state
		When I configure it for a scan
		Then the subarray must be in the READY state


	@XTP-16347
	Scenario: Abort configuring
        Given an subarray busy configuring
        When I command it to Abort
        Then the subarray should go into an aborted state

	@XTP-20114
	Scenario: Abort configuring Low
		Given an subarray busy configuring
		When I command it to Abort
		Then the subarray should go into an aborted state

