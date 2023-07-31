Feature: Assign resources to sdp subarray using the leaf node

	@XTP-16191
	Scenario: Assign resources to sdp low subarray using TMC leaf node
		Given a SDP subarray in the EMPTY state
		And a TMC SDP subarray Leaf Node
		When I start up the telescope
		When I assign resources to it without eb_id
		Then the SDP subarray throws an exception