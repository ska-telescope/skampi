@XTP-4413
Feature: Start up the telescope

	
	@XTP-4445 @XTP-3952 @XTP-3325
	Scenario: Start up the telescope
		Given the TMC
		When I start up the telescope
		Then the telescope must be on	

	
	