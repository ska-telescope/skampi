Feature: Assign resources to sdp subarray using the leaf node

	@XTP-16191
	Scenario: Assign resources to sdp low subarray using TMC leaf node
		Given a SDP subarray in the EMPTY state
		And a TMC SDP subarray Leaf Node
		When I assign resources to it
		Then the SDP subarray must be in IDLE state
		I release all resources assigned to it
		When I assign resources to it again
		Then the SDP subarray throws an exception