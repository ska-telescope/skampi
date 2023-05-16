# Make targets for conan artefacts

# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

ifeq ($(strip $(PROJECT)),)
  NAME=$(shell basename $(CURDIR))
else
  NAME=$(PROJECT)
endif

BASE = $(shell pwd)
CONAN_OUT_DIR ?= $(BASE)/build/## output directory for building conan packages

# list of conan packages
CONAN_PKG_DIRS := $(shell if [ -d conan ]; then cd conan; ls -d */ 2>/dev/null | sed 's/\/$$//'; fi;)
CONAN_PKGS ?= $(CONAN_PKG_DIRS)
CONAN_PKGS_TO_PUBLISH ?= $(CONAN_PKGS) 
CONAN_PKG ?= $(PROJECT_NAME)

SHELL=/bin/bash

# CPP_SRC is usually defined in cpp.mk - define if not included
ifndef CPP_SRC
CPP_SRC ?= src
endif

METADATA_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-metadata-support

CONAN_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-conan-support

CONAN_USER ?= marvin# user that will be used to build with conan 
CONAN_CHANNEL ?= stable# channel that will be used to build with conan

.PHONY: conan-pre-package conan-do-package conan-post-package conan-package \
	conan-publish conan-pre-publish conan-do-publish conan-publish-all conan-package-all

conan-pre-package:

conan-post-package:

conan-do-package: .release
	@echo "conan-package: package to build: $(CONAN_PKG) with User: $(CONAN_USER) and Channel: $(CONAN_CHANNEL) in: $(CONAN_OUT_DIR)"
	@. $(METADATA_SUPPORT); metadataGenerate "MANIFEST.skao.int"
	@. $(CONAN_SUPPORT); buildConan "$(CONAN_PKG)" "$(CPP_SRC)" "$(CONAN_OUT_DIR)" "$(CONAN_USER)" "$(CONAN_CHANNEL)"


## TARGET: conan-package
## SYNOPSIS: make conan-package
## HOOKS: conan-pre-package, conan-post-package
## VARS:
##       CONAN_PKG=<conan package directory in ./conan>
##       CONAN_CHANNEL=<default: stable> - channel that will be used to build with conan
##       CONAN_USER=<default: marvin> - user that will be used to build with conan
##       CONAN_OUT_DIR=<output directory for conan package> - default build/conan
##
##  Create a package file with the SKAO manifest file included and put the
##  output in CONAN_OUT_DIR.
conan-package: conan-pre-package conan-do-package conan-post-package  ## build the conan package

conan-pre-package-all:

conan-post-package-all:

conan-do-package-all:
	@echo "conan-package-all: packages to build: $(CONAN_PKGS) in: $(CONAN_OUT_DIR)"
	$(foreach conan_pkg,$(CONAN_PKGS), echo "$(conan_pkg)" ; make conan-package CONAN_PKG=$(conan_pkg) ;)

## TARGET: conan-package-all
## SYNOPSIS: make conan-package-all
## HOOKS: conan-pre-package-all, conan-post-package-all
## VARS:
##       CONAN_PKGS=<list of package sources in ./conan>
##       CONAN_OUT_DIR=<source directory for conan package> - default build/conan
##
##  Iterate over the list of CONAN_PKGS and execute conan-package for each, creating
##  the output files in CONAN_OUT_DIR.
conan-package-all: conan-pre-package-all conan-do-package-all conan-post-package-all  ## package all conan artefacts

conan-pre-publish:

conan-post-publish:

conan-do-publish:
	@echo "conan-publish: package to publish: $(CONAN_PKG) User: $(CONAN_USER) and Channel: $(CONAN_CHANNEL) in: $(CONAN_OUT_DIR)"
	@. $(CONAN_SUPPORT); publishConan "$(CONAN_PKG)" "$(CONAN_OUT_DIR)" "$(CONAN_USER)" "$(CONAN_CHANNEL)"


## TARGET: conan-publish
## SYNOPSIS: make conan-publish
## HOOKS: conan-pre-publish, conan-post-publish
## VARS:
##       CONAN_PKG=<conan package directory in ./conan>
##       CONAN_CHANNEL=<default: stable> - channel that will be used to build with conan
##       CONAN_USER=<default: marvin> - user that will be used to build with conan
##       CONAN_OUT_DIR=<output directory for conan package> - default build/conan
##
##  Publish the package file CONAN_PKG from directory in CONAN_OUT_DIR.
conan-publish: conan-pre-publish conan-do-publish conan-post-publish  ## publish the conan artefact to the repository

conan-pre-publish-all:

conan-post-publish-all:
## TARGET: conan-publish-all
## SYNOPSIS: make conan-publish-all
## HOOKS: conan-pre-publish-all, conan-post-publish-all
## VARS:
##       CONAN_PKGS=<list of conan package names> - defaults to list of ./conan directory names
##       CONAN_OUT_DIR=<output directory for conan package> - default build/conan
##
##  Publish the package files CONAN_PKGS from output in CONAN_OUT_DIR.

conan-do-publish-all:
	@echo "conan-publish-all: packages to publish: $(CONAN_PKGS_TO_PUBLISH) in: $(CONAN_OUT_DIR)"
	$(foreach conan_pkg,$(CONAN_PKGS_TO_PUBLISH), make conan-publish CONAN_PKG=$(conan_pkg) ;)

conan-publish-all: conan-pre-publish-all conan-do-publish-all conan-post-publish-all  ## publish all conan artefacts to the repository
# end of switch to suppress targets for help
endif
endif