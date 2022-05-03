@XTP-4639
Feature: Configure scan on csp subarray

    
    @XTP-4640 @XTP-5573 @XTP-3324
    Scenario: Configure scan on csp subarray in mid
        Given an CSP subarray in IDLE state
        When I configure it for a scan
        Then the CSP subarray must be in READY state    

    @XTP-4641 @XTP-5539 @XTP-3325
    Scenario: Configure scan on csp subarray in low
        Given an CSP subarray in IDLE state
        When I configure it for a scan
        Then the CSP subarray must be in READY state 
