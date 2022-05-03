@XTP-4769
Feature: Run a scan on CSP subarray


    @XTP-4771 @XTP-5573 @XTP-3324
    Scenario: Run a scan on csp subarray in mid
        Given an CSP subarray in READY state
        When I command it to scan for a given period
        Then the CSP subarray must be in SCANNING state

    @XTP-4772
    Scenario: Run a scan on csp subarray in low
        Given an CSP subarray in READY state
        When I command it to scan for a given period
        Then the CSP subarray must be in SCANNING state
