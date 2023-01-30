Feature: Start up the telescope with a script executed by the OET

	Scenario: Run the hello_world test script
		Given The OET is integrated with SKAMPI
		When the script is ran
		Then script execution completes successfully

	Scenario: Run the hello_world test script via an SB activity
		Given SB with id sbd-skampi-bdd-0001 and activity helloworld exists in ODA
		When I tell the OET to run helloworld activity for SBI sbd-skampi-bdd-0001
		Then script started by the activity completes successfully