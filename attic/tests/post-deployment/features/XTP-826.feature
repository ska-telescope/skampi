
	@XTP-826
	Scenario: Run more than one scan on a sub array
		Given a running telescope upon which a previously scan has successfully run
		Given I have configured it again
		When I run the scan again
		Then the scan should complete without any errors or exceptions
