.. _obs_apis:

Observation Execution APIs
**************************

The observation execution can be done by following a sequence of APIs as follows:

#. |resource_assignment|
#. |configure_scan_subarray_node|
#. |scan_subarray_node|
#. |end_subarray_node|
#. |release_resources|

Before performing any observation related operation it is necessary 
that the telescope is in ON state.

.. |resource_assignment| raw: html

    <a href="https://developer.skao.int/projects/ska-tmc-centralnode/en/latest/api/ska_tmc_centralnode.commands.html#ska-tmc-centralnode-commands-assign-resources-command-module" target="_blank">Resource assignment (Central Node)</a>

.. |configure_scan_subarray_node| raw: html

    <a href="https://developer.skao.int/projects/ska-tmc-subarraynode/en/latest/api/ska_tmc_subarraynode.commands.html#module-ska_tmc_subarraynode.commands.configure_command" target="_blank">Configure a scan (Subarray Node)</a>

.. |scan_subarray_node| raw: html

    <a href="https://developer.skao.int/projects/ska-tmc-subarraynode/en/latest/api/ska_tmc_subarraynode.commands.html#module-ska_tmc_subarraynode.commands.scan_command" target="_blank">Scan (Subarray Node)</a>

.. |end_subarray_node| raw: html

    <a href="https://developer.skao.int/projects/ska-tmc-subarraynode/en/latest/api/ska_tmc_subarraynode.commands.html#module-ska_tmc_subarraynode.commands.end_command" target="_blank">End (Subarray Node)</a>

.. |release_resources| raw: html

    <a href="https://developer.skao.int/projects/ska-tmc-centralnode/en/latest/api/ska_tmc_centralnode.commands.html#ska-tmc-centralnode-commands-release-resources-command-module" target="_blank">Releasing the resources (Central Node)</a>
