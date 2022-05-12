Feature: Make a set of dishes in full power state when assigned to a subarray

    Scenario: Make a set of dishes in full power state when assigned to a subarray
        Given a set of available dishes
        When I assign those dishes to a subarray
        Then those dishes shall be in full power