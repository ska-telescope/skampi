@XTP-18866
Feature: OET Non-SB observing happy path for SKA LOW

	#Scenario: Configure the low telescope subarray using OET
	@XTP-19864 @XTP-18866
	Scenario: Configure the low telescope subarray using OET
			Given an OET
			Given a valid scan configuration
			When I configure it for a scan
			Then the subarray must be in the READY state
