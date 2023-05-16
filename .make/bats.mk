# include Makefile for Helm Chart related targets and variables

# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

SHELL=/usr/bin/env bash

BASE_DIR ?= $(CURDIR)

BATS_CORE_VERSION ?= v1.4.1
BATS_SUPPORT_VERSION ?= v0.3.0
BATS_ASSERT_VERSION ?= v2.0.0
BATS_FILE_VERSION ?= v0.3.0
GIT_CLONE_ARGS ?= -c advice.detachedHead=false --quiet

BATS_TEST_TARGETS ?= tests/unit ## Targets for bats testing

## backwards compatibility
ifdef BATS_TEST_DIR
	BATS_TEST_TARGETS = $(BATS_TEST_DIR)
endif

.PHONY: bats-pre-install bats-do-install bats-post-install bats-install \
	bats-uninstall bats-pre-uninstall bats-do-uninstall

bats-reinstall: bats-uninstall bats-install ## reinstall bats-core dependencies

bats-pre-uninstall:

bats-post-uninstall:

bats-do-uninstall:
	@rm -rf $(BASE_DIR)/scripts/bats-*
	@echo "bats-uninstall: bats-core uninstalled"

## TARGET: bats-uninstall
## SYNOPSIS: make bats-uninstall
## HOOKS: bats-pre-uninstall, bats-post-uninstall
## VARS:
##       None.
##
##  Uninstall the bats test framework dependencies from /scripts/.

bats-uninstall: bats-pre-uninstall bats-do-uninstall bats-post-uninstall ## uninstall test dependencies for bats

bats-pre-install:

bats-post-install:

bats-do-install:
	@if [ -d $(BASE_DIR)/scripts/bats-core ]; then \
		echo "bats-install: Skipping install as bats-core already exists"; \
	else \
		echo "bats-install: Installing packages:"; \
		echo "  * bats-core=$(BATS_CORE_VERSION)"; \
		echo "  * bats-support=$(BATS_SUPPORT_VERSION)"; \
		echo "  * bats-assert=$(BATS_ASSERT_VERSION)"; \
		echo "  * bats-file=$(BATS_FILE_VERSION)"; \
		git clone $(GIT_CLONE_ARGS) --branch $(BATS_CORE_VERSION) https://github.com/bats-core/bats-core $(BASE_DIR)/scripts/bats-core; \
		git clone $(GIT_CLONE_ARGS) --branch $(BATS_SUPPORT_VERSION) https://github.com/bats-core/bats-support $(BASE_DIR)/scripts/bats-support; \
		git clone $(GIT_CLONE_ARGS) --branch $(BATS_ASSERT_VERSION) https://github.com/bats-core/bats-assert $(BASE_DIR)/scripts/bats-assert; \
		git clone $(GIT_CLONE_ARGS) --branch $(BATS_FILE_VERSION) https://github.com/bats-core/bats-file $(BASE_DIR)/scripts/bats-file; \
	fi

## TARGET: bats-install
## SYNOPSIS: make bats-install
## HOOKS: bats-pre-install, bats-post-install
## VARS:
##       None.
##
##  Install the bats test framework dependencies into /scripts/ from git.

bats-install: bats-pre-install bats-do-install bats-post-install ## install test dependencies for bats

## TARGET: bats-test
## SYNOPSIS: make bats-test
## HOOKS: bats-pre-test, bats-post-test
## VARS:
##       BATS_TEST_TARGETS=<set of bats files or directories containing .bats test files - defaults to ./tests/unit>
##
##  Execute bats (Bash Automated Testing System - https://github.com/bats-core/bats-core) shell tests.

bats-pre-test:

bats-post-test:

bats-test: bats-pre-test bats-install bats-do-test bats-post-test ## Run unit tests using BATS

bats-do-test:
	@echo "bats-test: The CI_JOB_ID=$(CI_JOB_ID)"
	rm -rf $(BASE_DIR)/build
	mkdir -p $(BASE_DIR)/build
	@cd $(BASE_DIR)/build && \
	TARGETS="" && \
	echo "bats-test: running:" && \
	for TARGET in $$(echo $(BATS_TEST_TARGETS) | sed 's#,# #g'); do \
		if [[ "$$TARGET" != /* ]]; then \
			TARGET="$(BASE_DIR)/$$TARGET"; \
		fi; \
		echo "* $$TARGET"; \
		TARGETS="$$TARGETS $$TARGET"; \
	done && \
	echo "bats-test: results in $$(pwd) ..." && \
	export CI_JOB_ID=$(CI_JOB_ID) && \
	$(BASE_DIR)/scripts/bats-core/bin/bats \
		--jobs 1 \
		--report-formatter junit \
		-o $(BASE_DIR)/build $$TARGETS


# end of switch to suppress targets for help
endif
endif
