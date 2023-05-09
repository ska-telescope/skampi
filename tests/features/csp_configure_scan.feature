@XTP-4639
Feature: Configure scan on csp subarray


    @XTP-4640 @XTP-5537 @XTP-4639 @XTP-3324 @XTP-5573
    Scenario: Configure scan on csp subarray in mid
        Given an CSP subarray in IDLE state
        When I configure it for a scan
        Then the CSP subarray must be in READY state

    @XTP-4641 @XTP-5537 @XTP-4639 @XTP-3325 @XTP-5539
    Scenario: Configure scan on csp subarray in low
        Given an CSP subarray in IDLE state
        When I configure it for a scan
        Then the CSP subarray must be in READY state

    @XTP-16346
	    Scenario: Abort configuring
        Given an subarray busy configuring
        When I command it to Abort
        Then the subarray should go into an aborted state

    @XTP-20129
    Scenario: Abort configuring on CSP Low
        Given an subarray busy configuring
        When I command it to Abort
        Then the subarray should go into an aborted state
