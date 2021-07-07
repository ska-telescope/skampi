Monitoring, alerts and bugs
===========================

The standard process for changing software includes the following phases:

* Problem/modification identification, classification, and prioritization
* Analysis
* Design
* Implementation
* Regression/system testing
* Acceptance testing
* Delivery

The above process is no different for triaging and managing a bug in skampi. In the present document we will focus on how to identify a problem or bug from incoming information and event notifications and how to assign it to the right team(s).

Problem identification
----------------------

The problem identification phase starts when there is an indication of a failure. This information can be raised by a developer (in any shared slack channel like the `team-system-support <https://skasoftware.slack.com/archives/CEMF9HXUZ>`_) or by an alert in the following slack channels:

* `ci-alerts-mvp <https://skasoftware.slack.com/archives/CPWKQBZV2>`_
* `prometheus-alerts <https://skasoftware.slack.com/archives/C0110QW8YMQ>`_

Any project member can join these channels to gain visibility of this information.

If the information comes from the `ci-alerts-mvp <https://skasoftware.slack.com/archives/CPWKQBZV2>`_ then the primary source of detailed information for analysis are the gitlab pipeline logs available `here <https://gitlab.com/ska-telescope/skampi/pipelines>`_.

Other source of information are:

* `kibana <http://192.168.93.94:5601/app/kibana>`_ (require `VPN <https://developer.skatelescope.org/en/latest/services/ait_performance_env.html#access-to-the-network-using-vpn>`_)
* `Node <http://alerts.engageska-portugal.pt:3000/d/rYdddlPWk/node-exporter-full>`_ dashboard
* `Gitlab runner <http://alerts.engageska-portugal.pt:3000/d/jTW2jWQmz/gitlab-runner-monitoring?orgId=1&refresh=5s>`_ dashboard
* `Gitlab CI Pipeline <http://alerts.engageska-portugal.pt:3000/d/gitlab_ci_pipeline_statuses/gitlab-ci-pipelines-statuses?orgId=1&refresh=30s>`_ dashboard
* `Docker monitoring <http://alerts.engageska-portugal.pt:3000/d/Kl_9tMRMk/docker-monitoring-with-node-selection?orgId=1>`_ dashboard
* `K8s cluster summary <http://alerts.engageska-portugal.pt:3000/d/taQlRuxik/k8s-cluster-summary?orgId=1&refresh=30s>`_ dashboard
* `Ceph Cluster <http://alerts.engageska-portugal.pt:3000/d/ZbYa7wqWk/ceph-cluster?orgId=1&refresh=30s>`_ dashboard
* `Elasticsearch <http://alerts.engageska-portugal.pt:3000/d/n_nxrE_mk/elasticsearch-dashboard?orgId=1&refresh=1m>`_ dashboard

Allocating ownership to teams
-----------------------------
The following are general rules for allocating ownership to teams:

* The primary responsibility for a failed pipeline is the owner of the first commit to the branch since the last successful run of the pipeline.  It is therfore the responsibility of the committer to follow up on the pipeline status after each git push.
* For every test case failing, the creator(s) of the test must be involved in order to assign the bug to the appropriate team.
* The System Team should be involved in the problem identification in order to understand whether the problem is infrastructure related (related to a k8s cluster or any layer below it - docker, VM, virtualization etc).
* For prometheus alerts, the system team must provide the analysis of the alert details in order to understand the cause, and give input into assigning it to the right team(s).

Raising bugs
------------

Bugs are raised following the `SKA Bug management <https://developer.skatelescope.org/en/latest/development_practices/ska_testing_policy_and_strategy.html#bug-management>`_ guidelines.



