@XTP-3361
Feature: Cucumber test results are uploaded to XRay
	#Cucumber test results are uploaded to XRay after CI job execution.

	
	@XTP-3346 @XTP-3347 @XTP-3348
	Scenario: SKAMPI CI Pipeline tests execute on SKAMPI
		Given a Continuous Integration Pipeline
		When an attempt is made to run tests within the repository
		Then the tests within the SKAMPI repository are run	

	#This test will always pass
	# @XTP-3362 @XTP-3347
	# Scenario Outline: An always passing test
	# 	Given a Continuous Integration Pipeline
	# 	When an attempt is made to run tests within the repository
	# 	Then there was a passing test