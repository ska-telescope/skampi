@XTP-3361
Feature: Cucumber test results are uploaded to XRay from k8s cluster
	#Cucumber test results are uploaded to XRay after CI job execution in a kubernetes cluster.

	
	@XTP-3346 @XTP-3347 @XTP-3348
	Scenario: SKAMPI CI Pipeline tests execute on SKAMPI
		Given a Continuous Integration Pipeline
		When an attempt is made to run tests within the repository
		Then the tests within the SKAMPI repository are run	

	#Tests if test results are going to be linked to the currently in-progress PI FixVersion after execution
	#This should be set in the test-exec.json file.
	@XTP-9480 @XTP-3347 @XTP-3348
	Scenario: Test if test-exec.json is configured to the latest Unreleased Version
		Given the SKA Jira project for Solution and System Acceptance Tests (skampi tests) with project key XTP
		And a test-exec.json file that contains a version parameter
		When integration tests are uploaded after tests executed in Skampi master branch pipelines
		Then the results will be associated with the Earliest Unreleased FixVersion in the XTP project
