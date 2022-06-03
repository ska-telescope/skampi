.. _ops_apis:

Operational Monitoring and Control APIs
****************************************

TMC provides APIs for controlling the telescope as follows:

* `TelescopeOn <https://developer.skao.int/projects/ska-tmc-centralnode/en/latest/api/ska_tmc_centralnode.commands.html#ska-tmc-centralnode-commands-telescope-on-command-module>`_
* `TelescopeOff <https://developer.skao.int/projects/ska-tmc-centralnode/en/latest/api/ska_tmc_centralnode.commands.html#ska-tmc-centralnode-commands-telescope-off-command-module>`_
* `Standby <https://developer.skao.int/projects/ska-tmc-centralnode/en/latest/api/ska_tmc_centralnode.commands.html#ska-tmc-centralnode-commands-telescope-standby-command-module>`_

To monitor the telescope, the Central Node exposes following attributes:

* ``telescopeState``
* ``healthState``