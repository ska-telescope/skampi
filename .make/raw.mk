# Make targets for raw artefacts

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

RAW_OUT_DIR ?= build/raw## output directory for building Raw packages

# list of raw packages
RAW_PKG_DIRS := $(shell if [ -d raw ]; then cd raw; ls -d */ 2>/dev/null | sed 's/\/$$//'; fi;)
RAW_PKGS ?= $(RAW_PKG_DIRS)

# list of raw packages on build
RAW_OUT_PKG_DIRS := $(shell if [ -d $(RAW_OUT_DIR) ]; then ls $(RAW_OUT_DIR)/*.tar.gz | sed 's/\/$$//'; fi;)
RAW_PKGS ?= $(RAW_OUT_PKG_DIRS)

SHELL=/bin/bash

METADATA_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-metadata-support

RAW_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-raw-support

.PHONY: raw-pre-package raw-do-package raw-post-package raw-package \
	raw-publish raw-pre-publish raw-do-publish raw-publish-all raw-package-all

raw-pre-package:

raw-post-package:

raw-do-package: .release
	@echo "raw-package: package to build: $(RAW_PKG) version: $(VERSION) in: $(RAW_OUT_DIR)"
	@. $(METADATA_SUPPORT); metadataGenerate "MANIFEST.skao.int"
	@. $(RAW_SUPPORT); buildRaw "$(RAW_PKG)" "$(VERSION)" "$(RAW_OUT_DIR)"

## TARGET: raw-package
## SYNOPSIS: make raw-package
## HOOKS: raw-pre-package, raw-post-package
## VARS:
##       RAW_PKG=<raw package directory in ./raw>
##       VERSION=<semver tag of image> - defaults to release key in .release file
##       RELEASE_CONTEXT=<directory holding .release file>
##       RAW_OUT_DIR=<output directory for raw package> - default build/raw
##
##  Create a tar.gz package file with the SKAO manifest file included and put the
##  output in RAW_OUT_DIR.

raw-package: raw-pre-package raw-do-package raw-post-package  ## build the raw package

raw-pre-package-all:

raw-post-package-all:

raw-do-package-all:
	@echo "raw-package-all: packages to build: $(RAW_PKGS) in: $(RAW_OUT_DIR)"
	$(foreach raw_pkg,$(RAW_PKGS), echo "$(raw_pkg)" ; make raw-package RAW_PKG=$(raw_pkg) ;)

## TARGET: raw-package-all
## SYNOPSIS: make raw-package-all
## HOOKS: raw-pre-package-all, raw-post-package-all
## VARS:
##       RAW_PKGS=<list of package sources in ./raw>
##       RAW_OUT_DIR=<source directory for raw package> - default build/raw
##
##  Iterate over the list of RAW_PKGS and execute raw-package for each, creating
##  the output .tar.gz files in RAW_OUT_DIR.

raw-package-all: raw-pre-package-all raw-do-package-all raw-post-package-all  ## package all raw artefacts

raw-pre-publish:

raw-post-publish:

raw-do-publish:
	@echo "raw-publish: package to publish: $(RAW_PKG) version: $(VERSION) in: $(RAW_OUT_DIR)"
	@. $(RAW_SUPPORT); publishRaw "$(RAW_PKG)" "$(VERSION)" "$(RAW_OUT_DIR)"

## TARGET: raw-publish
## SYNOPSIS: make raw-publish
## HOOKS: raw-pre-publish, raw-post-publish
## VARS:
##       RAW_PKG=<raw package name>
##       VERSION=<semver tag of image> - defaults to release key in .release file
##       RELEASE_CONTEXT=<directory holding .release file>
##       RAW_OUT_DIR=<output directory for raw package> - default build/raw
##
##  Publish the package file RAW_PKG from directory in RAW_OUT_DIR.

raw-publish: raw-pre-publish raw-do-publish raw-post-publish  ## publish the raw artefact to the repository

raw-pre-publish-all:

raw-post-publish-all:

## TARGET: raw-publish-all
## SYNOPSIS: make raw-publish-all
## HOOKS: raw-pre-publish-all, raw-post-publish-all
## VARS:
##       RAW_PKGS=<list of raw package names> - defaults to list of ./raw directory names
##       RAW_OUT_DIR=<output directory for raw package> - default build/raw
##
##  Publish the package files RAW_PKGS from output in RAW_OUT_DIR.

raw-do-publish-all:
	@echo "raw-publish-all: packages to publish: $(RAW_PKGS) in: $(RAW_OUT_DIR)"
	$(foreach raw_pkg,$(RAW_PKGS), make raw-publish RAW_PKG=$(raw_pkg) ;)

raw-publish-all: raw-pre-publish-all raw-do-publish-all raw-post-publish-all  ## publish all raw artefacts to the repository

# end of switch to suppress targets for help
endif
endif
