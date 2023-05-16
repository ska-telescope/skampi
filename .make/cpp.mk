# include Makefile for C++ related targets and variables

# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

ifeq ($(strip $(PROJECT)),)
  NAME=$(shell basename $(CURDIR))
else
  NAME=$(PROJECT)
endif

RELEASE_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-release-support

VERSION=$(shell . $(RELEASE_SUPPORT) ; RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; getVersion)
TAG=$(shell . $(RELEASE_SUPPORT); RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; getTag)

SHELL=/usr/bin/env bash


CPP_SRC ?= src## c++ src directory - defaults to src

.PHONY: cpp-pre-build cpp-do-build cpp-post-build cpp-build \
	cpp-lint cpp-pre-lint cpp-do-lint cpp-post-lint \
	cpp-test cpp-pre-test cpp-do-test cpp-post-test \
	cpp-publish cpp-pre-publish cpp-do-publish

cpp-pre-lint:

cpp-post-lint:

cpp-pre-build:

cpp-post-build:

cpp-pre-test:

cpp-post-test:

cpp-pre-publish:

cpp-do-build: .release
	echo "pass on build"

cpp-build: cpp-pre-build cpp-do-build cpp-post-build  ## build the C/C++ binary

cpp-do-test: .release
	echo "pass on test"

cpp-test: cpp-pre-test cpp-do-test cpp-post-test  ## test the C/C++ binary

cpp-publish: cpp-pre-publish cpp-do-publish  ## publish the conan artefact to the repository

cpp-do-publish:
	echo "pass on publish"

# end of switch to suppress targets for help
endif
endif
