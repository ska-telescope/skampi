# include Makefile for XRAY upload related targets and variables

# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

ifeq ($(strip $(PROJECT)),)
  NAME=$(shell basename $(CURDIR))
else
  NAME=$(PROJECT)
endif

XRAY_TEST_RESULT_FILE ?= "build/reports/cucumber.json"
XRAY_EXECUTION_CONFIG_FILE ?= "tests/xray-config.json"
XRAY_EXTRA_OPTS ?=
SHELL=/usr/bin/env bash

.PHONY: xray-publish xray-pre-publish xray-do-publish


## TARGET: xray-publish
## SYNOPSIS: make xray-publish
## HOOKS: xray-pre-publish, xray-post-publish
## VARS:
##       XRAY_TEST_RESULT_FILE=<path_to_file> - test result file
##       XRAY_EXECUTION_CONFIG=<path_to_file> - test execution config file
##       JIRA_AUTH=<token> - the token passed in
##
##  Publish BDD test results from this repository to XRAY.

xray-pre-publish:

xray-post-publish:

xray-publish: xray-pre-publish xray-do-publish xray-post-publish  ## publish BDD test results from this repository to XRAY
xray-do-publish:
	xray-upload -f $(XRAY_TEST_RESULT_FILE) -e $(XRAY_EXECUTION_CONFIG_FILE) $(XRAY_EXTRA_OPTS)

# end of switch to suppress targets for help
endif
endif
