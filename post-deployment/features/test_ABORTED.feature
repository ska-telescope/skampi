Feature: Recovering sub-array from error state

	Examples:
	| script 				            | obsstate	|
	| file:///app/scripts/restart.py	| EMPTY		|
	| file:///app/scripts/reset.py		| IDLE		|

	@test_ABORTED
	Scenario Outline: Recovering sub-array from ABORTED
		Given the sub-array is in ObsState ABORTED
		When I tell the OET to run <script>
		Then the sub-array goes to ObsState <obsstate>

	@test_ABORTED
	Scenario Outline: Recovering sub-array from FAULT
		Given the sub-array is in ObsState FAULT
		When I tell the OET to run <script>
		Then the sub-array goes to ObsState <obsstate>
