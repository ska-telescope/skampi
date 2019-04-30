Helm 
====
Helm is a tool for managing Kubernetes charts. Charts are packages of pre-configured Kubernetes resources.

The chart for this integration is composed by:

.. code-block:: console
	Chart.yaml          # A YAML file containing information about the chart
	LICENSE             # OPTIONAL: A plain text file containing the license for the chart
	README.md           # OPTIONAL: A human-readable README file
	requirements.yaml   # OPTIONAL: A YAML file listing dependencies for the chart
	values.yaml         # The default configuration values for this chart
	charts/             # A directory containing any charts upon which this chart depends.
	templates/          # A directory of templates that, when combined with values,
						# will generate valid Kubernetes manifest files.

.. code-block:: jaml
	# Chart.yaml
	apiVersion: v1
	appVersion: "1.0"
	description: A Helm chart for deploying the SKA Integration TMC-WEBUI on Kubernetes
	name: integration-tmc-webui
	version: 0.1.0

.. code-block:: jaml
	# example of values
	tmcprototype:
	  enabled: true
	  image:
		registry: nexus.engageska-portugal.pt/tango-example
		image: tmcprototype
		tag: latest
		pullPolicy: Always

