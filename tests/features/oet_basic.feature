Feature: Start up the telescope with a script executed by the OET

	Scenario: Run the hello_world test script
		Given The OET is integrated with SKAMPI
		When the script is ran
		Then script execution completes successfully
