Feature: Make a set of dishes go to full power

    @XTP-7118 @XTP-7117 @XTP-3324
    Scenario: Make a set of dishes go to full power state
        Given a set of available dishes
        When I switch those dishes to fullpower
        Then those dishes shall be in full power