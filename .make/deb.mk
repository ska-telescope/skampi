# Make targets for deb artefacts

# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

ifeq ($(strip $(PROJECT)),)
  NAME=$(shell basename $(CURDIR))
else
  NAME=$(PROJECT)
endif

DESCRIPTION ?= 'SKAO C++ project template'
PACKAGE_CONTACT ?= 'dev@test.local'
PACKAGE_MAINTAINER ?= 'Developer Name'

RELEASE_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-release-support

VERSION=$(shell . $(RELEASE_SUPPORT) ; RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; getVersion)
TAG=$(shell . $(RELEASE_SUPPORT); RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; getTag)

DEB_OUT_DIR ?= build/deb## output directory for building deb packages

SHELL=/bin/bash

METADATA_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-metadata-support

DEB_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-deb-support

.PHONY: deb-pre-package deb-do-package deb-post-package deb-package \
	deb-publish deb-pre-publish deb-do-publish

deb-pre-package:

deb-post-package:

deb-do-package: .release
	@echo "deb-package: package version to build: $(VERSION) in: $(DEB_OUT_DIR)"
	@. $(METADATA_SUPPORT); metadataGenerate "MANIFEST.skao.int"
	@. $(DEB_SUPPORT); buildDeb "$(VERSION)" "$(DEB_OUT_DIR)" "${DESCRIPTION}" "${PACKAGE_CONTACT}" "${PACKAGE_MAINTAINER}" "$(NAME)"

## TARGET: deb-package
## SYNOPSIS: make deb-package
## HOOKS: deb-pre-package, deb-post-package
## VARS:
##       VERSION=<semver tag of image> - defaults to release key in .release file
##       RELEASE_CONTEXT=<directory holding .release file>
##       DEB_OUT_DIR=<output directory for deb package> - default build/deb
##       ADDITIONAL_CMAKE_PARAMS=<additional params to pass to the cmake command> - default empty
##
##  Call cmake to generate an RPM artefact with the SKAO manifest metadata included and put the
##  output in DEB_OUT_DIR.

deb-package: deb-pre-package deb-do-package deb-post-package  ## build the deb package

deb-pre-publish:

deb-post-publish:

deb-do-publish:
	@echo "deb-publish: package version to publish: $(VERSION) in: $(DEB_OUT_DIR)"
	@. $(DEB_SUPPORT); publishDeb "$(DEB_OUT_DIR)" 

## TARGET: deb-publish
## SYNOPSIS: make deb-publish
## HOOKS: deb-pre-publish, deb-post-publish
## VARS:
##       VERSION=<semver tag of image> - defaults to release key in .release file
##       RELEASE_CONTEXT=<directory holding .release file>
##       DEB_OUT_DIR=<output directory for deb package> - default build/deb
##
##  Publish the RPM package from the DEB_OUT_DIR directory.

deb-publish: deb-pre-publish deb-do-publish deb-post-publish  ## publish the deb artefact to the repository

# end of switch to suppress targets for help
endif
endif
