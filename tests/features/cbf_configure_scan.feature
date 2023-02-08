@XTP-5587
Feature: Configure scan on cbf subarray

    @XTP-4601 @XTP-4600 @XTP-3324 @XTP-5588 @XTP-5590
    Scenario: Configure scan on cbf subarray in mid
        Given an CBF subarray in IDLE state
        When I configure it for a scan
        Then the CBF subarray must be in READY state    

    @XTP-4602 @XTP-4600 @XTP-3325 @XTP-5587 @XTP-5589
    Scenario: Configure scan on CBF low subarray
        Given an CBF subarray in IDLE state
        When I configure it for a scan
        Then the CBF subarray must be in READY state 
