Feature: Implement Alarm Handler and Integrate it into SKAMPI
    
    Scenario: Configure Alarm for EMPTY Observation State
        Given an TMC
        Given an telescope subarray
        Given an alarm handler
        When I assign resources to it
        When I configure alarm for Telescope with empty observation state
        Then alarm should be raised with UNACK state
