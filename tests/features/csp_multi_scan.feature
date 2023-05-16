Feature: Observations on CSP

    @XTP-19944
    Scenario: Run multiple scans on CSP subarray in mid for same scan type
        Given an subarray that has just completed it's first scan   
        When I command it to scan for a given period
		Then the CSP subarray must be in the SCANNING state until finished

    @XTP-19945
    Scenario: Run multiple scans on CSP subarray in mid for different scan types
        Given a subarray defined to perform scans for types .default and target:a
        Given a subarray configured for scan type .default
        And the subarray has just completed it's first scan for given configuration
        When I configure the subarray again for scan type target:a
        When I command it to scan for a given period
		Then the CSP subarray must be in the SCANNING state until finished

    @XTP-20102
    Scenario: Run multiple scans on CSP subarray in low for same scan type
        Given an subarray that has just completed it's first scan   
        When I command it to scan for a given period
		Then the CSP subarray must be in the SCANNING state until finished

    @XTP-20103
    Scenario: Run multiple scans on CSP subarray in low for different scan types
        Given a subarray defined to perform scans for types .default and target:a
        Given a subarray configured for scan type .default
        And the subarray has just completed it's first scan for given configuration
        When I configure the subarray again for scan type target:a
        When I command it to scan for a given period
		Then the CSP subarray must be in the SCANNING state until finished

