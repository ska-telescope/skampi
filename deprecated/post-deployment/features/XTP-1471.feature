Feature: Default

	
	@XTP-1469 @XTP-1471
	Scenario Outline: PSI1.1 test, Successfully configure the subarray for a scan
		Given a subarray with resources assigned
		And the subsystem Tango devices <devices> are in the IDLE obsState
		When I send the Configure command from the user interface to the TMC SubarrayNode
		Then the subsystem Tango devices <devices> will change to obsState CONFIGURING
		And change to the READY state after the subarray is fully prepared to scan
		
		Examples:
		|devices|
		|'TMC SubarrayNode,cspsubarray,cbfsubarray,sdpsubarray'|	

	
	@XTP-1470 @XTP-1471
	Scenario Outline: PSI1.2 test, Subarray successfully completing a scan
		Given the subarray is fully prepared to scan
		And the subsystem Tango devices <devices> are in the READY obsState
		When I send the Scan command from the user interface to the TMC SubarrayNode
		Then the subsystem Tango devices <devices> will change to obsState SCANNING
		And change to the READY state after the subarray completed the scan
		And produce a valid measurement set
		
		Examples:
		|devices|
		|'TMC SubarrayNode,cspsubarray,cbfsubarray,sdpsubarray|