Feature: Assign resources to sdp subarray using the leaf node


	Scenario: Error propagation
		Given a TMC SDP subarray Leaf Node
		When I start up the telescope
		When I assign resources for the second time with same eb_id
		Then the lrcr event throws error
		When I release all resources assigned to it
		Then the subarray must be in EMPTY state