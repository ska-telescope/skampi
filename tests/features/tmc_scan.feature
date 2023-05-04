@XTP-13150
Scenario: Run a scan from TMC
    Given an TMC
    Given a subarray in READY state
    When I command it to scan for a given period
    Then the subarray must be in the SCANNING state until finished

@XTP-16348 @XTP-22415 @XTP-20108 @XTP-16179 @XTP-16540 @XTP-3324 @Abort @Behavior @Monitoring @TMC @TMC_mid
Scenario: Abort scanning
    Given an subarray busy scanning
    When I command it to Abort
    Then the subarray should go into an aborted state

@XTP-16186 @XTP-16179 @XTP-3325 @XTP-16540 @Behavior @COM @Observation @TMC @TMC_low
Scenario: Run a scan on low subarray from TMC
    Given an TMC
    Given a subarray in READY state
    When I command it to scan for a given period
    Then the subarray must be in the SCANNING state until finished
