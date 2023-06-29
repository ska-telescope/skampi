# SKAMPI Documentation Contributions

This repository is a working space for any developers in SKA who want to integrate their products into the MVP. That is an overloaded sentence and needs unpacking to understand, but in simple terms, anyone developing subsystems of the SKA Software that can be installed in a Kubernetes cluster and work together with the other subsystems, is welcome to do so.

That means, anyone is also welcome to contribute to this documentation.

## Guidelines

* Do not document your own API in SKAMPI. SKAMPI is not a product, it is an integration environment. Add links to your subsystem API docs and basic usage guidelines only.
* Try to minimise outward facing links that may become deprecated over time. Add an entry-point to your own documentation space that can remain stable.
* Have the end-user of your documentation in mind when writing it.

## Readthedocs themes

Refer to the submodule ska-ser-sphinx-templates. This repo has been cloned into the SKAMPI docs/src repo but the steps given there (using `bootstrap.sh` to set up your repo) is not applicable to this one. Cherry-picking is strongly advised.
