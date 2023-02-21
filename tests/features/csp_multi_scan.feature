Feature: Observations on CSP


    Scenario: Run multiple scans on CSP subarray in mid for same scan type
        Given an subarray that has just completed it's first scan   
        When I command it to scan for a given period
		Then the CSP subarray must be in the SCANNING state until finished 
