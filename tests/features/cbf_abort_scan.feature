Feature: Test successful Abort Scan on CBF

    @XTP-21747
    Scenario: Test successful Abort Scan on CBF
        Given a subarray in aborted state whilst busy running a scan
        When I restart the subarray
        Then the subarray goes to EMPTY