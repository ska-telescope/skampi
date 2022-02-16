
Feature: Start up the telescope

	
	
	Scenario: Start up the telescope
		Given the TMC
		When I start up the telescope
		Then the telescope must be on	

	
	