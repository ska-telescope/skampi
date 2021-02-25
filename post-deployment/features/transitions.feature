Feature: Examples of using ska testing runway

  Examples:
    | nr_of_dishes  | subarray_id   | SB_config |
    | 2             | 1             | standard  |

  Background:
    Given A running telescope for executing observations on a subarray
    And An OET base API for commanding the telescope

  Scenario: Allocate dishes to a subarray using a predefined config
		When I allocate <nr_of_dishes> dishes to subarray <subarray_id> using the <SB_config> SB configuration
		Then The subarray is in the condition that allows scan configurations to take place

  Scenario: Configure a scan using a predefined config
    Given subarray <subarray_id> that has been allocated <nr_of_dishes> according to <SB_config>
    When I configure the subarray to perform a <scan_config> scan
    Then the subarray is in the condition to run a scan

    Examples:
      | scan_config |
      | standard    |

  Scenario: Abort resourcing
    Given subarray <subarray_id> busy resourcing due to an allocation of <nr_of_dishes> using the <SB_config> SB configuration
    When I give the command to Abort
    Then I expect the subarray to go the aborted state

  Scenario: Abort configuring
    Given a subarray <subarray_id> that has been allocated <nr_of_dishes> according to <SB_config>
    And that subarray is busy configuring in order to get ready to peforma a <scan_config> scan
    When I give the command to Abort
    Then I expect the subarray to cancel the configuration and go the aborted state$1
    Examples:
      | scan_config |
      | standard    |