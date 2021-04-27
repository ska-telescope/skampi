Feature: Examples of using ska testing runway

  Examples:
    | nr_of_dishes  | subarray_id   | SB_config |
    | 2             | 1             | standard  |

  Background:
    Given A running telescope for executing observations on a subarray
    And An OET base API for commanding the telescope

  Scenario: Configure a scan using a predefined config
    Given subarray <subarray_id> that has been allocated <nr_of_dishes> according to <SB_config>
    When I configure the subarray to perform a <scan_config> scan
    Then I expect the tmc subarray to transit to IDLE state when sdp and csp has done so

    Examples:
      | scan_config |
      | standard    |
