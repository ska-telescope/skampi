
@XTP-6189
Feature: Assign resources to subarray using TMC

@XTP-17275 @XTP-16540
	Scenario: Assign resources to subarray - happy flow
                Given the Telescope is in ON state
                And the subarray <subarray_id> obsState is EMPTY
                When I issue the assignResources command with the <resources_list> to the subarray <subarray_id>
                Then the subarray <subarray_id> obsState is IDLE
                And the correct resources <resources_list> are assigned
                Examples:  
                | subarray_id | resources_list                   |
                | 1          | P4, alveo 01, pst, csp_receptors  |
				| 3          | alveo 02, pss, sdp_receptors      |
