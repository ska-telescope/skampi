# Make targets for rpm artefacts

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

RPM_OUT_DIR ?= build/rpm## output directory for building rpm packages

SHELL=/bin/bash

METADATA_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-metadata-support

RPM_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-rpm-support

.PHONY: rpm-pre-package rpm-do-package rpm-post-package rpm-package \
	rpm-publish rpm-pre-publish rpm-do-publish

rpm-pre-package:

rpm-post-package:

rpm-do-package: .release
	@echo "rpm-package: package version to build: $(VERSION) in: $(RPM_OUT_DIR)"
	@. $(METADATA_SUPPORT); metadataGenerate "MANIFEST.skao.int"
	@. $(RPM_SUPPORT); buildRpm "$(VERSION)" "$(RPM_OUT_DIR)"

## TARGET: rpm-package
## SYNOPSIS: make rpm-package
## HOOKS: rpm-pre-package, rpm-post-package
## VARS:
##       VERSION=<semver tag of image> - defaults to release key in .release file
##       RELEASE_CONTEXT=<directory holding .release file>
##       RPM_OUT_DIR=<output directory for rpm package> - default build/rpm
##       ADDITIONAL_CMAKE_PARAMS=<additional params to pass to the cmake command> - default empty
##
##  Call cmake to generate an RPM artefact with the SKAO manifest metadata included and put the
##  output in RPM_OUT_DIR.

rpm-package: rpm-pre-package rpm-do-package rpm-post-package  ## build the rpm package

rpm-pre-publish:

rpm-post-publish:

rpm-do-publish:
	@echo "rpm-publish: package version to publish: $(VERSION) in: $(RPM_OUT_DIR)"
	@. $(RPM_SUPPORT); publishRpm "$(VERSION)" "$(RPM_OUT_DIR)"

## TARGET: rpm-publish
## SYNOPSIS: make rpm-publish
## HOOKS: rpm-pre-publish, rpm-post-publish
## VARS:
##       VERSION=<semver tag of image> - defaults to release key in .release file
##       RELEASE_CONTEXT=<directory holding .release file>
##       RPM_OUT_DIR=<output directory for rpm package> - default build/rpm
##
##  Publish the RPM package from the RPM_OUT_DIR directory.

rpm-publish: rpm-pre-publish rpm-do-publish rpm-post-publish  ## publish the rpm artefact to the repository

# end of switch to suppress targets for help
endif
endif
