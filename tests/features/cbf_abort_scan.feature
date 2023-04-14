@XTP-4599
Feature: Test successful Abort Scan on CBF

    Scenario: Test successful Abort Scan on CBF
        Given a subarray in aborted state whilst busy running a scan
        When I restart the subarray
        Then the subarray goes to EMPTY