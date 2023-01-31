@XTP-16179
Feature: TMC Integration Tests for Low

@XTP-16188
Scenario: Assign resources to csp low subarray using TMC leaf node
    Given a CSP subarray in the EMPTY state
    Given a TMC CSP subarray Leaf Node
    When I assign resources to it
    Then the CSP subarray must be in IDLE state
