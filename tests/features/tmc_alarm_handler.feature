Feature: Implement Alarm Handler and Integrate it into SKAMPI
    
    Scenario: Configure Alarm for IDLE Observation State
        Given an telescope subarray
        Given an Alarm handler configured for subarray obsState IDLE
        When I assign resources to it
        Then alarm must be raised with Unacknwoledged state
