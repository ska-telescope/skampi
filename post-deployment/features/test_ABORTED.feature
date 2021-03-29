@VTS-225
Feature: Verification of OET scripts being executed successfully during an observation


	@XTP-1773 @XTP-1772
	Scenario Outline: Recovering sub-array from ABORTED
		Given the sub-array is in ObsState ABORTED
		When I tell the OET to run <script>
		Then the sub-array goes to ObsState <obsstate>

		Examples:
		| script 				            | obsstate	|
		| file:///app/scripts/restart.py	| EMPTY		|
		| file:///app/scripts/reset.py		| IDLE		|


	@XTP-1774 @XTP-1772
	Scenario Outline: Recovering sub-array from FAULT
		Given the sub-array is in ObsState FAULT
		When I tell the OET to run <script>
		Then the sub-array goes to ObsState <obsstate>

		Examples:
		| script 				            | obsstate	|
		| file:///app/scripts/restart.py	| EMPTY		|
		| file:///app/scripts/reset.py		| IDLE		|


	@XTP-1775 @XTP-1772
	Scenario: Stopping script execution and sending Abort command to sub-array
		Given OET is executing script file:///app/scripts/observe_sb.py with SB scripts/data/long_sb.json
		When I stop the script execution using OET
		Then the script execution is terminated
		And abort.py script is run
		And the sub-array goes to ObsState ABORTED


	@XTP-1776 @XTP-1772
	Scenario: Stopping script execution without aborting sub-array
		Given OET is executing script file:///app/scripts/observe_sb.py with SB scripts/data/long_sb.json
		When I stop the script execution using OET setting abort flag to False
		Then the script execution is terminated
		And the sub-array ObsState is not ABORTED