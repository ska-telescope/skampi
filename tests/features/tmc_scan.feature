Feature: Scan the subarray using TMC
	@XTP-13150
	Scenario: Run a scan from TMC
		Given a TMC
        Given a subarray in READY state
        When I command it to scan for a given period
        Then the telescope subarray shall go from READY to SCANNING state
        Then the telescope subarray shall go back to READY when finished scanning