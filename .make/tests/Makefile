BASE = $(shell pwd)
ifneq (,$(wildcard help.mk))
-include *.mk
 else
-include ../*.mk
 endif

UNIT_TESTS ?= $(CURDIR)/../tests/unit
BATS_ARGS ?=

# define private rules and additional makefiles
-include ../PrivateRules.mak
-include python.mk

bats-reinstall: bats-uninstall bats-install ## reinstall bats-core dependencies

bats-uninstall:
	@rm -rf $(CURDIR)/../scripts/bats-*
	
bats-install:
	@if [ -d $(CURDIR)/../scripts/bats-core ]; then \
		echo "Skipping install as bats-core already exists"; \
	else \
		git clone --branch v1.5.0 https://github.com/bats-core/bats-core $(CURDIR)/../scripts/bats-core; \
		git clone --branch v0.3.0 https://github.com/bats-core/bats-support $(CURDIR)/../scripts/bats-support; \
		git clone --branch v2.0.0 https://github.com/bats-core/bats-assert $(CURDIR)/../scripts/bats-assert; \
	fi

test: bats-install ## Run unit tests using BATS
	rm -rf $(CURDIR)/../build
	mkdir -p $(CURDIR)/../build
	mkdir -p $(CURDIR)/../build/build/reports && mkdir -p $(CURDIR)/../build/build/results
	cd $(CURDIR)/../tests/resources/ && \
	cp -r images setup.cfg README.md setup.py CMakeLists.txt conan src altsrc pyproject.* terraform xray $(CURDIR)/../build/
	@cd $(CURDIR)/../build && \
	echo "running tests in: $$(pwd) ..." && \
	export PROJECT=tester && \
	$(CURDIR)/../scripts/bats-core/bin/bats $(BATS_ARGS) --report-formatter junit -o $(CURDIR)/../build $(UNIT_TESTS)
