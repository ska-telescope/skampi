@XTP-18844
Feature: Controlling the execution of a scan
	#As a user, I want to be able to control the execution of a scan, so that I can allow the telescope for multiple users.
	#
	#Implementation details are [here|https://confluence.skatelescope.org/display/SE/Run+a+scan+-+Implementation+Discussion+for+LOW+SUT+2.3]

	Background:
		#@XTP-18839
		Given the Telescope is in ON state
		
		#@XTP-18840
		Given the resources are assigned
		
		#@XTP-18841
		Given the scan configuration is applied
	
	@XTP-17103 @XTP-18844 @XTP-17101 @XTP-16540
	Scenario Outline: Execute a scan for the elapsed scan duration - happy flow
        Given the subarray <subarray_id> obsState is READY
		When the user issues the scan command with a <scan_id> to the subarray <subarray_id>
		Then the subarray <subarray_id> obsState transitions to SCANNING
		And  the subarray <subarray_id> obsState transitions to READY after the scan duration elapsed
		And the measurement set is present
		And the <scan_id> is correctly represented in the measurement set	
		Examples: 
		    | subarray_id   | scan_id   |  
		    |  1            | 123       |