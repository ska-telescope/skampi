@XTP-17877
Scenario: Configure for a scan on a subarray - happy flow
    Given the Telescope is in ON state
    And the subarray <subarray_id> obsState is IDLE
    When I issue the configure command with <scan_type/config_id> and <scan_configuration> to the subarray <subarray_id>
    Then the subarray <subarray_id> obsState is READY
    And the <scan_type/config_id> is correctly configured on the subarray <subarray_id>
    Examples: 
        | subarray_id   |  scan_configuration   |                  scan_type/config_id                             |
        |   1           |         tba           |       "science_A" / "sbi-mvp01-20200325-00001-science_A"         |