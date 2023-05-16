# Make targets for telescope model data artefacts

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

TMDATA_OUT_DIR ?= build/tmdata## output directory for building Raw packages

# Telescope model data directory
TMDATA_SRC_DIR ?= tmdata

SHELL=/bin/bash

METADATA_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-metadata-support

TMDATA_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-tmdata-support

.PHONY: tmdata-pre-package tmdata-do-package tmdata-post-package tmdata-package \
	tmdata-publish tmdata-pre-publish tmdata-do-publish tmdata-publish-all tmdata-package-all

tmdata-pre-package:

tmdata-post-package:

tmdata-do-package: .release
	@echo "tmdata-package: package to build: $(NAME)-tmdata in: $(TMDATA_OUT_DIR)"
	@. $(METADATA_SUPPORT); metadataGenerate "MANIFEST.skao.int"
	@. $(TMDATA_SUPPORT); buildTMData "$(TMDATA_SRC_DIR)" "$(TMDATA_OUT_DIR)"

## TARGET: tmdata-package
## SYNOPSIS: make tmdata-package
## HOOKS: tmdata-pre-package, tmdata-post-package
## VARS:
##       TMDATA_SRC_DIR=<directory holding telescope model data> - default tmdata
##       RELEASE_CONTEXT=<directory holding .release file>
##       TMDATA_OUT_DIR=<output directory for raw package> - default build/tmdata
##
##  Create a tar.gz package file with the SKAO manifest file included and put the
##  output in TMDATA_OUT_DIR.

tmdata-package: tmdata-pre-package tmdata-do-package tmdata-post-package  ## build the raw package

tmdata-pre-publish:

tmdata-post-publish:

tmdata-do-publish:
	@echo "tmdata-publish: package to publish: $(TMDATA_PKG) version: $(VERSION) in: $(TMDATA_OUT_DIR)"
	@. $(TMDATA_SUPPORT); publishTMData "$(TMDATA_SRC_DIR)" "$(TMDATA_OUT_DIR)" `git rev-parse HEAD` "${CI_COMMIT_TAG}" "${CI_COMMIT_BRANCH}" "${CI_MERGE_REQUEST_SOURCE_BRANCH_NAME}"

## TARGET: tmdata-publish
## SYNOPSIS: make tmdata-publish
## HOOKS: tmdata-pre-publish, tmdata-post-publish
## VARS:
##       RELEASE_CONTEXT=<directory holding .release file>
##       TMDATA_OUT_DIR=<output directory for raw package> - default build/raw
##
##  Publish the package file TMDATA_PKG from directory in TMDATA_OUT_DIR.

tmdata-publish: tmdata-pre-publish tmdata-do-publish tmdata-post-publish  ## publish the raw artefact to the repository

# end of switch to suppress targets for help
endif
endif
