Feature: Do resource management
	As an operator I want to manage subarray resources

Scenario: Deallocate Resources
	Given SKA Mid telescope
	Given The telescope is ready
	Given A subarray definition
	Given A resource allocation definition
	Given a means of observing the tmc subarray
	Given a means of observing the csp subarray
	Given a means of observing the csp master
	Given a means of observing the sdp subarray
	Given a means of observing the sdp master
	Given a monitor on the tmc subarray state
	Given a monitor on csp subarray state
	Given a monitor on sdp subarray state
	Given a way of monitoring receptor ID list
	Given I allocate resources to a subarray

	When I deallocate the resources

	Then subarray should go into OFF state

Scenario: Assign Resources
	Given A running telescope for executing observations on a subarray

	When I allocate two dishes to subarray 1

    Then I have a subarray composed of two dishes
	
	Then the subarray is in a state ready for executing observations by means of scheduling blocks

