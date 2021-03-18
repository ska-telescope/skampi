Feature: Default

	
	@XTP-1310
	Scenario Outline: PSI0.1 test, Initialise the TPM using the OET (Jupyter Notebook)
		Given subsystems <subsystem-list> are ONLINE and in the Tango Device OFF state
		And the Tile Tango Device is ONLINE and in the DISABLE state
		And the TPM_HW is powered ON and in the IDLE state
		When I send the command <command> to the TMC
		Then the TPM_HW will be programmed and initialized
		And the TPM_HW is in the WORKING state
		And the state and the temperature of the TPM_HW can be monitored.
		
		Examples:
		|subsystem-list|command|
		|'TMC CentralNode,MCCS Controller,MCCS Station1'|StartUpTelescope|
