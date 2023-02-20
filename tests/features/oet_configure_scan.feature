Scenario: Configure the low telescope subarray using OET
		Given an OET
		Given a low telescope subarray in IDLE state
		When I configure it for a scan and SBI /tests/resources/test_data/OET_integration/configure_low.json
		Then the subarray must be in the READY state
        