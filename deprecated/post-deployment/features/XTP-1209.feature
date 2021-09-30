Feature: 

	@skalow
	@XTP-1209 @XTP-1206
	Scenario Outline: TMC and MCCS subarray performs an observational scan
		Given Subarray is in ON state
		And Subarray is configured successfully
		When I call the execution of the scan command for duration of 10 seconds
		Then Subarray changes to a SCANNING state
		And Observation ends after 10 seconds as indicated by returning to READY state