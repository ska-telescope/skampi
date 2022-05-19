.. _apis:

Observation Execution APIs
**************************

The observation execution can be done by following a sequence of APIs as follows:

#. `Resource assignment (Central Node)<https://developer.skao.int/projects/ska-tmc-centralnode/en/latest/api/ska_tmc_centralnode.commands.html#ska-tmc-centralnode-commands-assign-resources-command-module>`
#. `Configure a scan (Subarray Node)<https://developer.skao.int/projects/ska-tmc-subarraynode/en/latest/api/ska_tmc_subarraynode.commands.html#module-ska_tmc_subarraynode.commands.configure_command>`
#. `Scan (Subarray Node)<https://developer.skao.int/projects/ska-tmc-subarraynode/en/latest/api/ska_tmc_subarraynode.commands.html#module-ska_tmc_subarraynode.commands.end_scan_command>`
#. `End (Subarray Node)<https://developer.skao.int/projects/ska-tmc-subarraynode/en/latest/api/ska_tmc_subarraynode.commands.html#module-ska_tmc_subarraynode.commands.end_command>`
#. `Releasing the resources (Central Node)https://developer.skao.int/projects/ska-tmc-centralnode/en/latest/api/ska_tmc_centralnode.commands.html#ska-tmc-centralnode-commands-release-resources-command-module`

Before performing any observation related operation it is necessary 
that the telescope is in ON state.