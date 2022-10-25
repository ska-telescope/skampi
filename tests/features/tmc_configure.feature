@XTP-XXXX
Feature: Configure subarray for a scan using TMC
	# @XTP-XXXX @XTP-XXXX @XTP-XXXX
	Scenario: Configure tmc-mid subarray for a scan
		Given an TMC
		Given an telescope subarray
		When I configure it for a scan
		Then the subarray must be in READY state
	