@XTP-4639
Feature: Configure scan on csp subarray

    
    @XTP-4640 @XTP-5537 @XTP-4639 @XTP-3324 @XTP-5573
    Scenario: Configure scan on csp subarray in mid
        Given an CSP subarray in IDLE state
        When I configure it for a scan
        Then the CSP subarray must be in READY state    
