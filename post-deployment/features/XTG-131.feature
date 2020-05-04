Feature: TMC integration with Dish Software

	@XTG-131
	Scenario: Dish from STANDBY-LP to STANDBY-FP
        Given Dish Master reports STANDBY-LP Dish mode
		When I command Dish Master to STANDBY-FP Dish mode
		Then Dish Master reports STANDBY-FP Dish mode
		And Dish Master (device) is in STANDBY state

	Scenario: Dish from STANDBY-FP to OPERATE
        Given Dish Master reports STANDBY-FP Dish mode
		When I command Dish Master to OPERATE Dish mode
		Then Dish Master reports OPERATE Dish mode
		And Dish Master (device) is in ON state	

	Scenario: Dish from OPERATE to STANDBY-FP
        Given Dish Master reports OPERATE Dish mode
		When I command Dish Master to STANDBY-FP Dish mode
		Then Dish Master reports STANDBY-FP Dish mode
		And Dish Master (device) is in STANDBY state

	Scenario: Dish from STANDBY-FP to STANDBY-LP
        Given Dish Master reports STANDBY-FP Dish mode
		When I command Dish Master to STANDBY-LP Dish mode
		Then Dish Master reports STANDBY-LP Dish mode
		And Dish Master (device) is in STANDBY state
