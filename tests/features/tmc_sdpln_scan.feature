@XTP-16179
Feature: TMC Integration Tests for Low

    @XTP-16193
    Scenario: Scan the SDP low using SDP leaf node
        Given an SDP subarray in READY state
        Given a TMC SDP subarray Leaf Node
        When I command it to scan for a given period
        Then the SDP subarray shall go from READY to SCANNING
        Then the SDP shall go back to READY when finished
