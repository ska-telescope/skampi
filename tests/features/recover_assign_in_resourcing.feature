	Scenario: fix skb-185
        Given an TMC
        And the resources are re-assigned to tmc with duplicate eb-id 
        And sdp subarray throws error and stays in obsState EMPTY
        And the resources are assigned to csp subarray 
        And the subarray node stucks in obsState RESOURCING
        When I release resources from the csp subarray
        Then csp subarray changes obsState to EMPTY
        And subarray node changes its obsState back to EMPTY


    Scenario: fix skb-230
        Given an TMC
        And the resources are re-assigned to tmc with duplicate eb-id
        And sdp subarray throws error and stays in obsState EMPTY
        And the resources are assigned to csp subarray
        And the subarray node stucks in obsState RESOURCING
        When I command it to Abort
        Then the subarray should go into an aborted state

 
