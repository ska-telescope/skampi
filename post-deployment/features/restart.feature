Scenario: Sub-array Invokes RESTART command
		Given A running telescope for executing observations on a subarray
		And I invoke AssignResources on Subarray
		And I call abort on subarray1
		When I invoke RESTART on subarray
		Then Sub-array changes to EMPTY state