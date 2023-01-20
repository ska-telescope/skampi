@XTP-17101
Feature: Start the SUT's components,assign resources,configure a scan,wait for completion,then check SDP results through the QA interface

  @XTP-17103
  Scenario: Verify QA interface of the SDP
    Given the SUT's components have started
    And resources have been assigned
    And a scan is configured
    When the scan is completed
    Then SDP results are as expected
    And the metrics are displayed in the QA Display