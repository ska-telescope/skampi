@XTP-17101
Feature: Start the SUT's components,assign resources,configure a scan,wait for completion,then check SDP results through the QA interface

  @XTP-17103 @hello
  Scenario Outline: Run a scan on a subarray - happy flow
    Given the subarray <subarray_id> obsState is READY
    When the user issues the scan command with a <scan_id> to the subarray <subarray_id>
    Then the subarray <subarray_id> obsState transitions to SCANNING
    And the subarray <subarray_id> obsState transitions to READY after the scan duration elapsed
    And the measurement set is present
    And the <scan_id> is correctly represented in the measurement set

    Examples:
      | subarray_id | scan_id |
      | 01            | 123       |