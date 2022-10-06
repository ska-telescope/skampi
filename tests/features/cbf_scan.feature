@XTP-4764
Feature: Run a scan on CBF subarray


    @XTP-4767 @XTP-5588 @XTP-4764 @XTP-3324
    Scenario: Run a scan on cbf subarray in mid
        Given an CBF subarray in READY state
        When I command it to scan for a given period
        Then the CBF subarray must be in the SCANNING state until finished

    @XTP-4768 @XTP-5587 @XTP-4764 @XTP-3325
    Scenario: Run a scan on cbf subarray in low
        Given an CBF subarray in READY state
        When I command it to scan for a given period
        Then the CBF subarray must be in the SCANNING state until finished
