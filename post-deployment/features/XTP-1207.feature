Feature: 

	@skalow
	@XTP-1207 @XTP-1206
	Scenario Outline: TMC and MCCS subarray resource allocation
		Given A running telescope for executing observations on a subarray
		When I allocate resources to TMC and MCCS Subarray
		Then The TMC and MCCS subarray is in the condition that allows scan configurations to take place