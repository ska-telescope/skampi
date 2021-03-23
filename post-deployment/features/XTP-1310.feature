Feature: Default

	
	@XTP-1310
	Scenario: PSI0.1 test, Initialise the TPM using the OET (Jupyter Notebook)
		Given subsystems are ONLINE (with Tango Device in OFF state,except MccsTile in the DISABLE or OFF state)
		And the TPM_HW is powered ON and in the IDLE state
		
		When I send the command ON to the TMC
		Then the TPM_HW will be programmed and initialized
		And the TPM_HW is in the WORKING state
		And the state and the temperature of the TPM_HW can be monitored
		
