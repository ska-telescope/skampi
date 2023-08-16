@XTP-22638
Feature: Invalid configuration handling

	
	@XTP-16109 @XTP-22419 @XTP-6186 @XTP-3324 @COM @Resource_Management @TMC
	Scenario: Assign resources with duplicate id
		Given an TMC
		Given an telescope subarray
		When I assign resources with a duplicate sb id
		Then the subarray should throw an exception and remain in the previous state