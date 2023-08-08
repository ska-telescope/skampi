Feature: Assign resources to sdp subarray using the leaf node


	Scenario: Error propagation
		Given a TMC SDP subarray Leaf Node
		When I assign resources to the subarray for two times
		Then the lrcr event throws error