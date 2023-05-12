@XTP-4769
Feature: Run a scan on CSP subarray


    @XTP-4771 @XTP-5537 @XTP-4769 @XTP-3324 @XTP-5573
    Scenario: Run a scan on csp subarray in mid
        Given an CSP subarray in READY state
        When I command it to scan for a given period
        Then the CSP subarray must be in the SCANNING state until finished

    @XTP-4772 @XTP-5537 @XTP-4769 @XTP-3325 @XTP-5539
    Scenario: Run a scan on csp subarray in low
        Given an CSP subarray in READY state
        When I command it to scan for a given period
        Then the CSP subarray must be in the SCANNING state until finished

    @XTP-16345
    Scenario: Abort Csp scanning
        Given an subarray busy scanning
        When I command it to Abort
        Then the subarray should go into an aborted state

    @XTP-20128
    Scenario: Abort scanning on CSP Low
        Given an subarray busy scanning
        When I command it to Abort
        Then the subarray should go into an aborted state

