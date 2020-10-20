
Feature: Execute a basic observation for the MVP subarray using OET pubsub mechanism

	#@pytest.mark.skip(reason="no way of currently testing this")
	Scenario: Sub-array resource allocation-deallocation using OET pubsub
		Given A running telescope for executing observations on a subarray with enabling oet pubsub
		When I allocate 2 dishes to subarray 1
		Then I have a subarray composed of 2 dishes
		And resources are successfully assigned

