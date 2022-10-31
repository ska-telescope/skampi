Feature: Verification of configure a scan using a predefined config on subarray node
 
  Scenario: Configure a scan using a predefined config
    Given subarray <subarray_id> that has been allocated <nr_of_dishes> according to <SB_config>
    When I configure the subarray to perform a <scan_config> scan
    Then the subarray is in the condition to run a scan

    Examples:
      | scan_config |
      | standard    |