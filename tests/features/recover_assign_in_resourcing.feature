	Scenario: fix skb-185
        Given an TMC
        And the resources are re-assigned to tmc with duplicate eb-id 
        And sdp subarray throws error and stays in obsState EMPTY
        And the resources are assigned to csp subarray 
        And the subarray node stucks in obsState RESOURCING
        When I release resources from the csp subarray
        Then csp subarray changes obsState to EMPTY
 
