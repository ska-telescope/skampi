Feature: Configure scan on cbf subarray

    Scenario: Configure scan on cbf subarray in mid
        Given an CBF subarray in IDLE state
        When I configure it for a scan
        Then the CBF subarray must be in READY state    

    Scenario: Configure scan on cbf subarray in low
        Given an CBF subarray in IDLE state
        When I configure it for a scan
        Then the CBF subarray must be in READY state 
