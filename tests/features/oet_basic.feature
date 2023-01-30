Feature: Start up the telescope with a script executed by the OET

	Scenario: Run the hello_world test script
		Given The OET is integrated with SKAMPI
		When the script is ran
		Then script execution completes successfully

	Scenario: Run the hello_world test script via an SB activity
		Given The OET is integrated with SKAMPI
		When I tell the OET to run allocate activity for SBI sbd-skampi-bdd-0001
		Then script execution completes successfully