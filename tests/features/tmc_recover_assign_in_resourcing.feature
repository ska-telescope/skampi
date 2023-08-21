@XTP-3325 @XTP-27257
Scenario: Fix bug skb-185 in TMC
    Given an TMC
    And the resources are re-assigned to tmc with duplicate eb-id 
    And the sdp subarray throws an error and remains in obsState EMPTY
    And the resources are assigned to csp subarray 
    And the subarray node is stuck in obsState RESOURCING
    When I release the resources from the csp subarray
    Then the csp subarray changes its obsState to EMPTY
    And the subarray node changes its obsState back to EMPTY