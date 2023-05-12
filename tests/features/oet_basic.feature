Feature: Start up the telescope with a script executed by the OET

	Scenario: Run the hello_world test script
		Given The OET is integrated with SKAMPI
		When the script file:///tmp/oda/hello_world.py is run
		Then script execution completes successfully

	@AT-489-36
	Scenario: Run the hello_world test script via an SB activity
		Given a test SB with activity helloworld exists in ODA
		When I tell the OET to run helloworld activity on the test SB
		Then script started by the activity completes successfully