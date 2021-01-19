    @XTP-1156
    Scenario: Observation Execution Tool
        Given The Observation Execution Tool create command
        When OET create is given a <file> that does not exist
        Then the OET returns an <error>

        Examples:
      | file                       | error                                                            |
      | file:///FileNotFound.py    | FileNotFoundError: No such file or directory: /FileNotFound.py   |
      | sdljfsdjkfhsd              | ValueError: Script URI type not handled: sdljfsdjkfhsd           |
