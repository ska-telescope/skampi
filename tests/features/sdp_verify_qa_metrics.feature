@XTP-17101
Feature: Start the SUT's components,assign resources,configure a scan,wait for completion,then check SDP results through the QA interface

  @XTP-17103
  Scenario Outline: Run a scan on a subarray - happy flow
    Given the Telescope is in ON state
    And the subarray <subarray_id> obsState is READY
    When I issue the scan command with a <scan_ID> to the subarray <subarray_id>
    Then the subarray <subarray_id> obsState transitions to SCANNING
    And the subarray <subarray_id> obsState transitions to READY when the scan completes
    And the measurement set is present
    And the <scan_ID> is correctly represented in the measurement set

    Examples:
      | <subarray_id> | <scan_ID> |
      | 01            | 123       |
      | 01            | 555       |