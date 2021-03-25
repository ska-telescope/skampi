Feature: Default

	#*Scenario: SKA Mid Scheduling Block Resource Allocation and Observation*
	#
	#_OST sends to OET a request for resource allocation followed by a request for observing the same Scheduling Block - Resources are allocated to the subarray and the scheduling block is observed_
	#
	#The main objective of this test is to confirm that if we use the Observation Execution Tool to allocate resources and then execute an observation of a Scheduling Block that the subarray goes through the expected set of state transitions.
	#
	#The expected set of state transitions is defined in [ADR-8|https://confluence.skatelescope.org/pages/viewpage.action?pageId=105416556] .
	#
	#*Notes on the scenario outline*
	#
	#For the purposes of the test *READY* is treated as a transitory state that is allowed but not explicitly tested for since the time the subarray spends in the READY state is sometimes too short to be detectable with polling.
	#
	#The Scheduling Block used for this test is the example_sb.json within the OET Scripts project which defines a science scan and a calibration scan and each of these scans is repeated twice (so 4 scans in total).
	# * For the Resource Allocation the script used is allocate_from_file_sb.py and the subarray will pass through the states *EMPTY -> RESOURCING -> IDLE*
	#
	# * For the Observing the script used is observe_sb.py and each observation will pass through *CONFIGURING -> SCANNING* once for each scheduled scan in the SB
	#
	#Once the observation is complete the subarray should return to the *IDLE* state
	@XTP-966 @XTP-968
	Scenario: SKA Mid Scheduling Block - Resource allocation and observation
		Given the subarray ska_mid/tm_subarray_node/1 and the SB scripts/data/example_sb.json
		When the OET allocates resources for the SB with the script file://scripts/allocate_from_file_sb.py
		Then the OET observes the SB with the script file://scripts/observe_sb.py
		Then the SubArrayNode obsState passes in order through the following states EMPTY, RESOURCING, IDLE, CONFIGURING, SCANNING, CONFIGURING, SCANNING, CONFIGURING, SCANNING, CONFIGURING, SCANNING, IDLE