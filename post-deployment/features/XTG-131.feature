Feature: TMC integration with Dish Software

	@XTG-131
	Scenario: Dish to full power standby mode
        	Given Dish Master reports STANDBY_LP Dish mode
		When I command Dish Master to STANDBY_FP Dish mode
		Then Dish Master reports STANDBY_FP Dish mode
		And Dish Master (device) is in STANDBY state
