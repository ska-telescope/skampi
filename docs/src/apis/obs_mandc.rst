.. _obs_apis:

Observation Execution APIs
**************************

The observation execution can be done by following a sequence of APIs as follows:

#. |resource_assignment|
#. |configure_scan|
#. `Scan (Subarray Node) <https://developer.skao.int/projects/ska-tmc-subarraynode/en/latest/api/ska_tmc_subarraynode.commands.html#module-ska_tmc_subarraynode.commands.end_scan_command>`_
#. `End (Subarray Node) <https://developer.skao.int/projects/ska-tmc-subarraynode/en/latest/api/ska_tmc_subarraynode.commands.html#module-ska_tmc_subarraynode.commands.end_command>`_
#. `Releasing the resources (Central Node) <https://developer.skao.int/projects/ska-tmc-centralnode/en/latest/api/ska_tmc_centralnode.commands.html#ska-tmc-centralnode-commands-release-resources-command-module>`_

Before performing any observation related operation it is necessary 
that the telescope is in ON state.

.. |resource_assignment| raw: html

    <a href="https://developer.skao.int/projects/ska-tmc-centralnode/en/latest/api/ska_tmc_centralnode.commands.html#ska-tmc-centralnode-commands-assign-resources-command-module">Resource assignment (Central Node)</a>

.. |configure_scan| raw: html

    <a href="https://developer.skao.int/projects/ska-tmc-subarraynode/en/latest/api/ska_tmc_subarraynode.commands.html#module-ska_tmc_subarraynode.commands.configure_command">Configure a scan (Subarray Node) </a>
