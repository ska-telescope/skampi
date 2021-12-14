@XTP-3361
Feature: Cucumber test results are uploaded to XRay from k8s cluster
	#Cucumber test results are uploaded to XRay after CI job execution in a kubernetes cluster.

	
	@XTP-3346 @XTP-3347 @XTP-3348
	Scenario: SKAMPI CI Pipeline tests execute on SKAMPI
		Given a Continuous Integration Pipeline
		When an attempt is made to run tests within the repository
		Then the tests within the SKAMPI repository are run