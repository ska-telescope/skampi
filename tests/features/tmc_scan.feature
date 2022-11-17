@XTP-13150
Scenario: Run a scan from TMC
    Given an TMC
    Given a subarray in READY state
    When I command the TMC to run a scan
    Then the telescope subarray shall go back to READY when finished scanning


    