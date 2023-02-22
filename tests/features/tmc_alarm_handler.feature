Feature: Implement Alarm Handler and Integrate it into SKAMPI
    
    @XTP-19625 @XTP-3324
    Scenario: Configure Alarm for IDLE Observation State
        Given an telescope subarray
        Given an Alarm handler configured to raise an alarm when the subarray obsState is IDLE
        When I assign resources to it
        Then alarm must be raised with Unacknowledged state
