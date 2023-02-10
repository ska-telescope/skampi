"""
The feature and scenarios were discussed at
https://confluence.skatelescope.org/display/SE/Mid+Test+Plan+PI17+-+SUT1.8
"""

# what Requirement does this belong to? Should we add its XTP id?

Feature: SUT1 repeats commands successfully

	@XTP-17520
	Background:
		Given the CSP LMC Subarray is On and its obsState is Empty
		And the Mid CBF Subarray is On and its obsState is Empty
		And the SDP Subarray is On and its obsState is Empty
		

	@XTP-16846 @XTP-16844 @XTP-16379
	Scenario: SUT1 runs a single scan successfully
		When I run AssignResources on the CSP LMC and the SDP
		And I run Configure on the CSP LMC and the SDP
		And I run Scan and after 10 seconds run EndScan on the CSP LMC and the SDP
		And I run End and then ReleaseAllResources on the CSP LMC and the SDP

		Then the data received by the SDP matches the data sent by the CBF

	@XTP-17574 @XTP-16844 @XTP-16379
	Scenario: SUT1 repeats scans with same resources successfully
		When I run AssignResources on the CSP LMC and the SDP
		And I run Configure on the CSP LMC and the SDP
		And I run Scan and after 10 seconds run EndScan on the CSP LMC and the SDP
		And I repeat the Scan and EndScan commands once more
		And I run End and then ReleaseAllResources on the CSP LMC and the SDP

		Then the data received by the SDP matches the data sent by the CBF
		And each scan can be identified by its associated metadata

	@XTP-17576 @XTP-16844 @XTP-16379
	Scenario: SUT1 runs two scans of different types and produces the scan data with correct metadata
		When I run AssignResources on the CSP LMC and the SDP
		And the configuration string requests two scans of different types
		And I run Configure on the CSP LMC and the SDP of the first scan type
		And I run Scan and after 10 seconds run EndScan on the CSP LMC and the SDP
		And I run Configure on the CSP LMC and the SDP of the second scan type
		And I run Scan and after 10 seconds run EndScan on the CSP LMC and the SDP
		And I run End and then ReleaseAllResources on the CSP LMC and the SDP

		Then the data received by the SDP matches the data sent by the CBF
		And each scan can be identified by its associated metadata
		And there is one scan per scan type

	@XTP-17579 @XTP-16844 @XTP-16379
	Scenario: SUT1 repeats scans with new resources and produces the scan data with correct metadata
		When I run AssignResources with some resources on the CSP LMC and the SDP
		And I run Configure on the CSP LMC and the SDP
		And I run Scan and after 10 seconds run EndScan on the CSP LMC and the SDP
		And I run End and then ReleaseAllResources on the CSP LMC and the SDP
		And I repeat all When steps with different resources

		Then the data received by the SDP matches the data sent by the CBF
		And each scan can be identified by its associated metadata
		And the associated execution block IDs match the ones specified by the relevant AssignResources command