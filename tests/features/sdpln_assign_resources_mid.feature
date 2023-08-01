Feature: Assign resources to sdp subarray using the leaf node

	@XTP-16191
	Scenario: Assign resources to sdp low subarray using TMC leaf node
		Given a SDP subarray in the EMPTY state
		And a TMC SDP subarray Leaf Node
		When I start up the telescope
		When I assign resources for the first time 
		Then the SDP subarray must be in IDLE state
		When I assign resources to it again
		When I release all resources assigned to it