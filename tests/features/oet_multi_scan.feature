Feature: Observations on OET

    Scenario: Run multiple scans on mid subarray for same scan type from OET
        Given an OET
        Given an subarray that has just completed it's first scan   
        When I command it to scan for a given period
		Then the subarray must be in the SCANNING state until finished
