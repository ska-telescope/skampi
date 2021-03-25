Feature: Telescope startup and standby

	@XTP-1001
    Scenario: Starting up telescope
        Given telescope is in OFF State
        When I tell the OET to run <script>
        Then the central node goes to state <state>


    @XTP-1002
    Scenario: Starting up telescope
        Given telescope is in ON State
        When I tell the OET to run <script>
        Then the central node goes to state <state>

        Examples:
      | script                            | state  |
      | file:///app/scripts/startup.py    | ON     |
      | file:///app/scripts/startup.py    | OFF    |
