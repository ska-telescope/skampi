Feature: Make a set of dishes go to full power state when assigned to a subarray

    @XTP-7118 @XTP-7117 @XTP-3324
    Scenario: Make a set of dishes go to full power state when assigned to a subarray
        Given a set of available dishes
        When I assign those dishes to a subarray
        Then those dishes shall be in full power