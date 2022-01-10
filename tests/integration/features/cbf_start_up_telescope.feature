@XTP-3969
Feature: Start up the cbf

	
	@XTP-3966 @XTP-3967 @XTP-3325
	Scenario: Start up the cbf in low
		Given an CBF
		When I start up the telescope
		Then the cbf must be on	

	
	@XTP-3968 @XTP-3967 @XTP-3324
	Scenario: Start up the cbf in mid
		Given an CBF
		When I start up the telescope
		Then the cbf must be on