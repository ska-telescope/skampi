@XTP-16179
Feature: TMC Integration Tests for Low

    @XTP-16192
    Scenario: Configure the SDP low using SDP leaf node
        Given an SDP subarray in the IDLE state
        Given a TMC SDP subarray Leaf Node
        When I configure it for a scan
        Then the SDP subarray shall go from IDLE to READY state
