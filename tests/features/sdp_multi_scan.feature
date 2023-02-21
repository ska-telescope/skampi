Feature: Observations on sdp


    Scenario: Run multiple scans on SDP subarray in mid for same scan type
        Given an subarray that has just completed it's first scan   
        When I command it to scan for a given period
		Then the SDP subarray must be in the SCANNING state until finished 

    Scenario: Run multiple scans on SDP subarray in mid for different scan types
        Given a subarray defined to perform scans for types .default and target:a
        Given a subarray configured for scan type .default
        And the subarray has just completed it's first scan for given configuration
        When I configure the subarray again for scan type target:a
        When I command it to scan for a given period
		Then the SDP subarray must be in the SCANNING state until finished
