@VTS-225
Feature: Verification of OET scripts being executed successfully during an observation

	#*Scenario: Releasing resources of sub-array*
	@XTP-782 @XTP-776
	Scenario: Releasing resources of sub-array
		Given the sub-array is in ObsState IDLE
		When I tell the OET to run file:///app/scripts/deallocate.py
		Then the sub-array goes to ObsState EMPTY