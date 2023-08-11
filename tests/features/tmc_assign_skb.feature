Feature: Verify SKB-185 in TMC 


	Scenario: Verification of skb-185
		Given an TMC
		And I assign resources and release for the first time from the central node
		When I assign resources for the second time with same eb_id
		Then the tmc throws error and stays in obsState EMPTY