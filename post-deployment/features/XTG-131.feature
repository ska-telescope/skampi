Feature: TMC integration with Dish Software

	@XTG-131
	Scenario: mid_d0001/elt/master from STANDBY-LP to STANDBY-FP
        Given mid_d0001/elt/master reports STANDBY-LP Dish mode
		When I command mid_d0001/elt/master to STANDBY-FP Dish mode
		Then mid_d0001/elt/master reports STANDBY-FP Dish mode
		And mid_d0001/elt/master is in STANDBY state

	Scenario: mid_d0001/elt/master from STANDBY-FP to OPERATE
        Given mid_d0001/elt/master reports STANDBY-FP Dish mode
		When I command mid_d0001/elt/master to OPERATE Dish mode
		Then mid_d0001/elt/master reports OPERATE Dish mode
		And mid_d0001/elt/master is in ON state

	Scenario: mid_d0001/elt/master from OPERATE to STANDBY-FP
        Given mid_d0001/elt/master reports OPERATE Dish mode
		When I command mid_d0001/elt/master to STANDBY-FP Dish mode
		Then mid_d0001/elt/master reports STANDBY-FP Dish mode
		And mid_d0001/elt/master is in STANDBY state

	Scenario: mid_d0001/elt/master from STANDBY-FP to STANDBY-LP
        Given mid_d0001/elt/master reports STANDBY-FP Dish mode
		When I command mid_d0001/elt/master to STANDBY-LP Dish mode
		Then mid_d0001/elt/master reports STANDBY-LP Dish mode
		And mid_d0001/elt/master is in STANDBY state

	Scenario: mid_d0005/elt/master from STANDBY-LP to STANDBY-FP
        Given mid_d0005/elt/master reports STANDBY-LP Dish mode
		When I command mid_d0005/elt/master to STANDBY-FP Dish mode
		Then mid_d0005/elt/master reports STANDBY-FP Dish mode
		And mid_d0005/elt/master is in STANDBY state

	Scenario: mid_d0005/elt/master from STANDBY-FP to OPERATE
        Given mid_d0005/elt/master reports STANDBY-FP Dish mode
		When I command mid_d0005/elt/master to OPERATE Dish mode
		Then mid_d0005/elt/master reports OPERATE Dish mode
		And mid_d0005/elt/master is in ON state

	Scenario: mid_d0005/elt/master from OPERATE to STANDBY-FP
        Given mid_d0005/elt/master reports OPERATE Dish mode
		When I command mid_d0005/elt/master to STANDBY-FP Dish mode
		Then mid_d0005/elt/master reports STANDBY-FP Dish mode
		And mid_d0005/elt/master is in STANDBY state

	Scenario: mid_d0005/elt/master from STANDBY-FP to STANDBY-LP
        Given mid_d0005/elt/master reports STANDBY-FP Dish mode
		When I command mid_d0005/elt/master to STANDBY-LP Dish mode
		Then mid_d0005/elt/master reports STANDBY-LP Dish mode
		And mid_d0005/elt/master is in STANDBY state
