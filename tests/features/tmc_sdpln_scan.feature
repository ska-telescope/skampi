@XTP-16193
Scenario: Scan the sdp low using csp leaf node
    Given an SDP subarray in the READY state
    Given a TMC SDP subarray Leaf Node
    When I command it to scan for a given period
    Then the SDP subarray shall go from READY to SCANNING
    Then the SDP shall go back to READY when finished