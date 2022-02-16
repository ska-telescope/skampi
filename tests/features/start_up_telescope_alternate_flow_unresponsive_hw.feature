@USE-1
Feature: Startup Telescope

    @XTP-4731 @XTP-4737
    Scenario: Start up the telescope
        Given a specific HW is unresponsive
        When I start up the telescope
        Then the telescope must not be on
        Then the error message is shown in the HMI