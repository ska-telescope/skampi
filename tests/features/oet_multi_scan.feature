@VTS-225
Feature: Verification of OET scripts being executed successfully during an observation

    #*Scenario: Run multiple scans on TMC subarray in low same scan type*
    @XTP-21538 @XTP-18866
    Scenario: Run multiple scans on TMC subarray in low for same scan type
        Given an OET
        Given an subarray that has just completed it's first scan
        When I command it to scan for a given period
		Then the subarray must be in the SCANNING state until finished

    #*Scenario: Run multiple scans on TMC subarray in low different scan type*
    @XTP-21541 @XTP-18866
    Scenario: Run multiple scans on TMC subarray in low for different scan type
        Given an OET
        Given a subarray defined to perform scans for types .default and target:a
        Given a subarray configured for scan type .default
        And an subarray that has just completed it's first scan
        When I configure the subarray again for scan type target:a
        When I command it to scan for a given period
		Then the subarray must be in the SCANNING state until finished

    #*Scenario: Run multiple scans on TMC subarray in mid same scan type*
    @XTP-21542 @XTP-2328
    Scenario: Run multiple scans on mid subarray for same scan type from OET
        Given an OET
        Given an subarray that has just completed it's first scan   
        When I command it to scan for a given period
        Then the subarray must be in the SCANNING state until finished

    #*Scenario: Run multiple scans on TMC subarray in mid different scan type*
    @XTP-21543 @XTP-2328
    Scenario: Run multiple scans on mid subarray for different scan type from OET
        Given an OET
        Given a subarray defined to perform scans for types .default and target:a
        Given a subarray configured for scan type .default
        And an subarray that has just completed it's first scan
        When I configure the subarray again for scan type target:a
        When I command it to scan for a given period
        Then the subarray must be in the SCANNING state until finished