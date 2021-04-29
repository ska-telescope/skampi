Feature: Examples of using ska testing runway

  Examples:
    | nr_of_dishes  | subarray_id   | SB_config |
    | 2             | 1             | standard  |

  Background:
    Given A running telescope for executing observations on a subarray


  Scenario: TMC subarray transitions to READY after sdp/csp subarray
    Given subarray <subarray_id> that has been allocated <nr_of_dishes> according to <SB_config>
    When I configure the subarray to perform a <scan_config> scan
    Then the tmc subarray transits to READY state after sdp subarray and csp subarray has done so

    Examples:
      | scan_config |
      | standard    |
