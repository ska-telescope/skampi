Feature: Default

	#allowed modes include ["OFF", "STARTUP", "SHUTDOWN", "STANDBY_LP", "STANDBY_FP", "MAINTENANCE", "CONFIG", "OPERATE"]
	@XTP-3090 @XTP-3085 @PI11
	Scenario: Test dish stow request
		Given dish reports any allowed dish mode
		When I execute a stow command
		Then the dish mode should report STOW
		Then the elevation should be almost equal to the stow position
		Then the azimuth should remain in the same position
