	Scenario: fix skb-185
        Given an TMC
        And the resources are assigned with <eb_id> and released on the subarray 
        And resources are again assigned to the subarray with same eb_id <eb_id>
        And sdp subarray throws error and stays in obsState EMPTY
        And the resources are assigned to csp subarray 
        And the subarray node stucks in obsState RESOURCING
        When I release resources from the csp subarray
        Then csp subarray changes obsState to EMPTY
        And subarray node changes its obsState back to EMPTY 
        Examples:  
            | eb_id |
            | eb-mvp01-20230809-49670          | 
