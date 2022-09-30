@XTP-4600
Feature: Configure scan on CBF subarray

    
    @XTP-4601 @XTP-5588 @XTP-5537 @XTP-4639 @XTP-3324 @XTP-5573
    Scenario: Configure scan on cbf subarray in mid
        Given an CBF subarray in IDLE state
        When I configure it for a scan
        Then the CBF subarray must be in READY state    

    @XTP-4602 @XTP-4676 @XTP-4639 @XTP-3325 @XTP-5539
    Scenario: Configure scan on cbf subarray in low
        Given an CBF subarray in IDLE state
        When I configure it for a scan
        Then the CBF subarray must be in READY state 