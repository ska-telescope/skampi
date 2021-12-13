@XTP-3361
Feature: Cucumber test results are uploaded to XRay from k8s cluster
	#Cucumber test results are uploaded to XRay after CI job execution in a kubernetes cluster.

	
	@XTP-3346 @XTP-3347 @XTP-3348
	Scenario: SKAMPI CI Pipeline tests execute on SKAMPI
		Given a Continuous Integration Pipeline
		When an attempt is made to run tests within the repository
		Then the tests within the SKAMPI repository are run	

	#This test is aimed at ensuring that a kubernetes cluster can perform basic functionality and is heavily dependent on all the fixtures that are described in the test code itself, instead of relying on explicitly stating what the cluster configuration should look like.
	#
	#This might be changed in future.
	@XTP-3362 @XTP-3347 @XTP-3348
	Scenario: Kubernetes cluster basic tests
		Given a service nginx1 exposing a deployment nginx1
		And a service nginx2 exposing a deployment nginx2
		When I write to the shared volume via the nginx1 service
		Then the result of a curl to both services is the same
