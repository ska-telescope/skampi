Triaging and managing Skampi (SKB) bugs
=======================================

This document defines a process for Triaging and managing Skampi (SKB) bugs so that any SKA team member knows how to handle the funnel of incoming bugs, the allocation, distribution and management of them.

The standard process for changing a software includes the following phases: 

* Problem/modification identification, classification, and prioritization
* Analysis
* Design
* Implementation
* Regression/system testing
* Acceptance testing
* Delivery

The above process is not different for triaging and managing a bug in skampi. In the present document we will focus on how to identify a information as problem/bug and how to assign it to the right team(s).

Problem identification
----------------------

The problem identification phase starts when there is an indication of a failure. This information can be raised by a developer (in any shared slack channel like the `team-system-support <https://skasoftware.slack.com/archives/CEMF9HXUZ>`_) or by an alert in the following slack channels:

* `ci-alerts-mvp <https://skasoftware.slack.com/archives/CPWKQBZV2>`_
* `prometheus-alerts <https://skasoftware.slack.com/archives/C0110QW8YMQ>`_

Everyone can join the channels to get those kind of information. 

If the information comes from the `ci-alerts-mvp <https://skasoftware.slack.com/archives/CPWKQBZV2>`_ then the primary source of information if the gitlab pipeline logs available `here <https://gitlab.com/ska-telescope/skampi/pipelines>`_. 

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

* For every test case failing, the creator(s) of it must be involved in order to assign the bug to a specific team. 
* System team should be always involved in the problem identification in order to understand whether the problem is infrastructual (related to a k8s cluster or any layer below it - docker, VM, virtualization and so on).
* For prometheus alerts, the system team must provide the analisys of the problem and in case assign it to the right team(s).



