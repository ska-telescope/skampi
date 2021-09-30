Feature: 

	@skalow
	@XTP-1208 @XTP-1206
	Scenario Outline: TMC and MCCS subarray transitions from IDLE to READY state
		Given A running telescope for executing observations on a subarray
		And Subarray is in IDLE state
		When I call the configure scan execution instruction
		Then Subarray is in READY state for which subsequent scan commands can be directed to deliver a basic imaging outcome