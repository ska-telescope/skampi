	
    Scenario: fix skb-185		  
        Given a TMC 
		And the resources are assigned and released on the subarray 
		And resources are again assigned to the subarray with same eb_id	
		And sdp subarray throws error and stays in obsState EMPTY
        And the resources are assigned to csp subarray 
        And the subarray node stucks in obsState Resourcing
        when I release resources from the csp subarray
        then csp subarray changes obsState to EMPTY
        And subarray node changes its obsState back to EMPTY 