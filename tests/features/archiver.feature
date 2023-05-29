
@SP-3254
Feature: Finalize the EDA deployment and configuration approach
	#There are some concerns over the existing approach to deploying and configuring the EDA. The scope of this enabler is to work out a solution that enables fulfilling the requirements of the developer team as well as addresses the concerns of the System team. The solution should specify:
	# # Way to deploy EDA for
	# ## Mid and Low
	# ## Various ska environments: dev, operation sandbox, PSI, ITF
	# # Way to administer the EDA configuration so that attributes of various subsystem devices are archived
	# ## At the time of deployment
	# ## Additions/modifications/deletions once the system is deployed
	# # Any security concerns
	# # Follow the best practices in k8s
	#
	#It is possible that separate approaches for different environments but having a single approach is better

@SP-3255
Feature: Update the EDA deployment solution as per the outcome of SP-3254
	#This feature is to implement the solution as per the outcome of the enabler SP-3254.
	#
	#TBD: add more description

	
	@XTP-20577 @XTP-20576 @COM @EDA @Entry_point @TMC @XTP-3324
	Scenario: Configure an EDA database instance for Mid
		Given a EDA database instance
		Given an EDA configuration service
		Given an EDA archive configuration file specifying subarray obsstate to be archived
		Given an telescope subarray
		When I upload the configuration file
		When I assign resources to the subarray
		Then the subarray went to obststate to IDLE event must be archived

	
	@XTP-20578 @XTP-20576 @COM @EDA @Entry_point @TMC @XTP-3324
	Scenario: Archive an change event on EDA database instance for Mid
		Given an telescope subarray
		Given a EDA database instance configured to archive an change event on the subarray obsstate
		When I assign resources to the subarray
		Then the subarray went to obststate to IDLE event must be archived

	
	@XTP-20579 @XTP-20576 @COM @EDA @Entry_point @TMC @configuration @XTP-3325
	Scenario: Configure an EDA database instance for Low
		Given a EDA database instance
		Given an EDA configuration service
		Given an EDA archive configuration file specifying subarray obsstate to be archived
		Given an telescope subarray
		When I upload the configuration file
		When I assign resources to the subarray
		Then the subarray went to obststate to IDLE event must be archived

	
	@XTP-20580 @XTP-20576 @TMC_low @XTP-3325
	Scenario: Archive an change event on EDA database instance for Low
		Given an telescope subarray
		Given a EDA database instance configured to archive an change event on the subarray obsstate
		When I assign resources to the subarray
		Then the subarray went to obststate to IDLE event must be archived
