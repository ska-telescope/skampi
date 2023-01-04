
Feature: Assign Release resources on sdp leaf node


      @XTP-16191
      Scenario:  Assign Release resources on sdp subarray in low using the leaf node
        Given a SDP subarray in the EMPTY state
        Given a TMC SDP subarray Leaf Node
        When I assign resources to it
        Then the SDP subarray must be in IDLE state

