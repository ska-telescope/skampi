Feature: 

	@skamid
	@XTP-4444
	Scenario Outline: BDD test case for Abort command Invoked while subarry is in configuring
		Given a running telescope upon which a previously configure scan is run
		When I call abort command
		Then The subarray eventually transitions into obsState ABORTED