Feature: Implement Alarm Handler and Integrate it into SKAMPI
    
    @XTP-19625
    Scenario: Configure Alarm for IDLE Observation State
        Given an telescope subarray
        Given an Alarm handler configured for subarray obsState IDLE
        When I assign resources to it
        Then alarm must be raised with Unacknowledged state
