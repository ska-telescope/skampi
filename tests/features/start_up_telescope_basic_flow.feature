@USE-1
Feature: Startup Telescope

    @XTP-4445 @XTP-3952 @XTP-3325
    Scenario: Start up the telescope
        Given all SW and HW is operational
        When I start up the telescope
        Then the telescope must be on