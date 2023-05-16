# include Makefile for OCI Image related targets and variables

# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

ifeq ($(strip $(PROJECT_NAME)),)
  PROJECT_NAME=$(shell basename $(CURDIR))
endif

RELEASE_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-release-support
OCI_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-oci-support
OCI_IMAGE_SCRIPT_DIR := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))
OCI_NEXUS_REPO=docker-internal

VERSION=$(shell . $(RELEASE_SUPPORT) ; RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; getVersion)
TAG=$(shell . $(RELEASE_SUPPORT); RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; getTag)

SHELL=/usr/bin/env bash

# User defined variables
CAR_OCI_REGISTRY_HOST ?= ## OCI Image Registry
ifeq ($(strip $(CAR_OCI_REGISTRY_HOST)),)
  CAR_OCI_REGISTRY_HOST = artefact.skao.int
endif
OCI_IMAGE_BUILD_CONTEXT ?= .  ## Image build context directory, relative to ./images/<image dir> for multiple images, gets replaced by `$(PWD)` for single images where Dockerfile is in the root folder. Don't use `.` to provide root folder for multiple images, use `$(PWD)`.
OCI_IMAGE_FILE_PATH ?= Dockerfile ## Image recipe file
OCI_IMAGE_DIRS := $(shell if [ -d images ]; then cd images; for name in $$(ls); do if [ -d $$name ]; then echo $$name; fi done else echo $(PROJECT_NAME);  fi;)
OCI_IMAGES ?= $(OCI_IMAGE_DIRS) ## Images to lint and build
OCI_IMAGES_TO_PUBLISH ?= $(OCI_IMAGES) ## Images to publish
OCI_IMAGE ?= $(PROJECT_NAME) ## Default Image (from /images/<OCI_IMAGE dir>)
OCI_BUILDER ?= docker ## Image builder eg: docker, or podman
OCI_BUILD_ADDITIONAL_ARGS ?= ## Additional build argument string
OCI_LINTER ?= hadolint/hadolint:v2.9.2
OCI_SKIP_PUSH ?= ## OCI Skip the push
OCI_TOOLS_IMAGE ?= artefact.skao.int/ska-tango-images-pytango-builder:9.3.12
OCI_BUILD_ADDITIONAL_TAGS ?= ## Additional OCI tags to be built and published as part of build process. Note that: This won't affect publish jobs

.PHONY: oci-pre-build oci-image-build oci-post-build oci-build \
	oci-publish oci-pre-publish oci-do-publish oci-post-publish

oci-pre-lint:

oci-post-lint:

oci-image-lint:
	@. $(OCI_SUPPORT) ; OCI_BUILDER=$(OCI_BUILDER) \
	OCI_LINTER=$(OCI_LINTER) \
	OCI_IMAGE_FILE_PATH=$(OCI_IMAGE_FILE_PATH) \
	ociImageLint "$(OCI_IMAGES)"

## TARGET: oci-lint
## SYNOPSIS: make oci-lint
## HOOKS: oci-pre-lint, oci-post-lint
## VARS:
##       OCI_BUILDER=[docker|podman] - OCI executor for linter
##       OCI_LINTER=<hadolint image> - OCI Image of linter application
##       OCI_IMAGE_FILE_PATH=<build file usually Dockerfile>
##       OCI_IMAGES=<list of image directories under ./images/>
##
##  Perform lint checks on a list of OCI Image build manifest files found
##  in the specified OCI_IMAGES directories.

oci-lint: oci-pre-lint oci-image-lint oci-post-lint  ## lint the OCI image

oci-pre-build:

oci-post-build:

oci-image-build: .release
	@echo "oci-image-build:Building image: $(OCI_IMAGE) registry: $(CAR_OCI_REGISTRY_HOST) context: $(OCI_IMAGE_BUILD_CONTEXT)"
	@. $(OCI_SUPPORT) ; \
	export OCI_IMAGE_BUILD_CONTEXT=$(OCI_IMAGE_BUILD_CONTEXT); \
	export OCI_IMAGE_FILE_PATH=images/$(strip $(OCI_IMAGE))/$(OCI_IMAGE_FILE_PATH); \
	if [[ -f Dockerfile ]]; then \
		echo "This is a oneshot OCI Image project with Dockerfile in the root OCI_IMAGE_BUILD_CONTEXT=$(PWD)"; \
		export OCI_IMAGE_BUILD_CONTEXT=$(PWD); \
		export OCI_IMAGE_FILE_PATH=$(OCI_IMAGE_FILE_PATH); \
	fi; \
	PROJECT_NAME=$(PROJECT_NAME) \
	CAR_OCI_REGISTRY_HOST=$(CAR_OCI_REGISTRY_HOST) \
	OCI_BUILDER=$(OCI_BUILDER) \
	VERSION=$(VERSION) \
	OCI_IMAGE=$(strip $(OCI_IMAGE)) \
	TAG=$(TAG) \
	OCI_BUILD_ADDITIONAL_ARGS="$(OCI_BUILD_ADDITIONAL_ARGS) --build-arg http_proxy --build-arg https_proxy --build-arg CAR_OCI_REGISTRY_HOST=$(CAR_OCI_REGISTRY_HOST)" \
	OCI_BUILD_ADDITIONAL_TAGS="$(OCI_BUILD_ADDITIONAL_TAGS)" \
	OCI_SKIP_PUSH=$(OCI_SKIP_PUSH) \
	OCI_NEXUS_REPO=$(OCI_NEXUS_REPO) \
	ociImageBuild "$(strip $(OCI_IMAGE))"

# default to skipping on the push if CI_JOB_ID is unset or 'local'
# as you cannot push to the repository without the CI pipeline credentials
ifeq ($(CI_JOB_ID),)
OCI_SKIP_PUSH=yes
else ifeq ($(CI_JOB_ID),local)
OCI_SKIP_PUSH=yes
endif

## TARGET: oci-build
## SYNOPSIS: make oci-build
## HOOKS: oci-pre-build, oci-post-build
## VARS:
##       OCI_IMAGE=<image directory under ./images/> is the name of the image to build
##       OCI_IMAGE_BUILD_CONTEXT=<path to image build context> relative to ./images/<image dir> for multiple images, gets replaced by `$(PWD)` for single images where Dockerfile is in the root folder. Don't use `.` to provide root folder for multiple images, use `$(PWD)`.
##       OCI_IMAGE_FILE_PATH=<build file usually Dockerfile>
##       CAR_OCI_REGISTRY_HOST=<defaults to artefact.skao.int>
##       VERSION=<semver tag of image> - defaults to release key in .release file
##       RELEASE_CONTEXT=<directory holding .release file>
##       OCI_BUILDER=[docker|podman] - OCI executor for building images
##       OCI_BUILD_ADDITIONAL_ARGS=<any additional arguments to pass to OCI_BUILDER>
##       OCI_SKIP_PUSH=<set non-empty to skip push after build>
##       OCI_BUILD_ADDITIONAL_TAGS=<set as list of additional oci tags for build jobs> - defaults to empty
##
##  Perform an OCI Image build, and optionally push to the project GitLab registry
##  If a Dockerfile is found in the root of the project then the project is
##  deemed to be a one-shot image build with a OCI_IMAGE_BUILD_CONTEXT of the
##  entire project folder passed in. If there are multiple images under `images/` folder
##  OCI_IMAGE_BUILD_CONTEXT is set as the ./images/<image dir>.
##  A .dockerignore file should be placed in
##  the root of the project to limit the files/directories passed into the build
##  phase, as excess files can impact performance and have unintended consequences.
##  The image tag defaults to $VERSION-dev.c$CI_COMMIT_SHORT_SHA when pushing to $CI_REGISTRY
##  otherwise it will be $VERSION.
##  $VERSION is the current release key in the RELEASE_CONTEXT .release file.  The
##  RELEASE_CONTEXT defaults to the root folder of the project, but can be overriden
##  if .release files are required per image to build.  See ska-tango-images for an example.
##  When running oci-build inside the CI pipeline templates, CAR_OCI_REGISTRY_HOST is set to
##  ${CI_REGISTRY}/${CI_PROJECT_NAMESPACE}/${CI_PROJECT_NAME}, so that the image is automatically
##  pushed to the GitLab CI registry for the related project.

oci-build: oci-pre-build oci-image-build oci-post-build  ## build the OCI_IMAGE image (from /images/<OCI_IMAGE dir>)


oci-pre-build-all:

oci-post-build-all:

oci-do-build-all:
	$(foreach ociimage,$(OCI_IMAGES), make oci-build CAR_OCI_REGISTRY_HOST=$(CAR_OCI_REGISTRY_HOST) OCI_IMAGE=$(ociimage); rc=$$?; if [[ $$rc -ne 0 ]]; then exit $$rc; fi;)

## TARGET: oci-build-all
## SYNOPSIS: make oci-build-all
## HOOKS: oci-pre-build-all, oci-post-build-all
## VARS:
##       OCI_IMAGES=<list of image directories under ./images/> names of the images to build
##       OCI_IMAGE_FILE_PATH=<build file usually Dockerfile>
##       CAR_OCI_REGISTRY_HOST=<defaults to artefact.skao.int>
##       OCI_BUILDER=[docker|podman] - OCI executor for building images
##       OCI_BUILD_ADDITIONAL_ARGS=<any additional arguments to pass to OCI_BUILDER>
##       OCI_SKIP_PUSH=<set non-empty to skip push after build>
##
##  Perform an OCI Image build for a list of images by iteratively calling oci-build - see above.

oci-build-all: oci-pre-build-all oci-do-build-all oci-post-build-all  ## build all the OCI_IMAGES image (from /images/*)

oci-pre-publish:

oci-post-publish:

oci-do-publish: VERSION := $(shell . $(RELEASE_SUPPORT) ; RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; getVersion)
oci-do-publish:
	@. $(OCI_SUPPORT) ; \
	export OCI_NEXUS_REPO=$(OCI_NEXUS_REPO); \
	echo "oci-do-publish: Checking for $(OCI_IMAGE) $(VERSION)"; \
	res=$$(ociImageExists "$(OCI_IMAGE)" "$(VERSION)"); \
	echo "oci-do-publish: Image check returned: $$res"; \
	if [[ "$$res" == "0" ]]; then \
		echo "oci-publish:WARNING: $(CAR_OCI_REGISTRY_HOST)/$(OCI_IMAGE):$(VERSION) already exists, skipping "; \
		exit 0; \
	else \
		echo "oci-do-publish: Pulling $${CI_REGISTRY}/$${CI_PROJECT_NAMESPACE}/$${CI_PROJECT_NAME}/$(OCI_IMAGE):$(VERSION)"; \
		$(OCI_BUILDER) pull $${CI_REGISTRY}/$${CI_PROJECT_NAMESPACE}/$${CI_PROJECT_NAME}/$(OCI_IMAGE):$(VERSION); \
		$(OCI_BUILDER) tag $${CI_REGISTRY}/$${CI_PROJECT_NAMESPACE}/$${CI_PROJECT_NAME}/$(OCI_IMAGE):$(VERSION) $(CAR_OCI_REGISTRY_HOST)/$(OCI_IMAGE):$(VERSION); \
		echo "oci-do-publish: Pushing to $(CAR_OCI_REGISTRY_HOST)/$(OCI_IMAGE):$(VERSION)"; \
		$(OCI_BUILDER) push $(CAR_OCI_REGISTRY_HOST)/$(OCI_IMAGE):$(VERSION); \
	fi

## TARGET: oci-publish
## SYNOPSIS: make oci-publish
## HOOKS: oci-pre-publish, oci-post-publish
## VARS:
##       OCI_IMAGES=<list of image directories under ./images/> names of the images to publish
##       CAR_OCI_REGISTRY_HOST=<defaults to artefact.skao.int>
##       OCI_BUILDER=[docker|podman] - OCI executor for publishing images
##       VERSION=<semver tag of image> - defaults to release key in .release file
##       RELEASE_CONTEXT=<directory holding .release file>
##
##  Publish a list of images to the CAR_OCI_REGISTRY_HOST.  This requires the source image to have
##  been already built and pushed to the ${CI_REGISTRY}.
##  The image to publish is pulled from:
##  ${CI_REGISTRY}/${CI_PROJECT_NAMESPACE}/${CI_PROJECT_NAME}/$(OCI_IMAGE):$(VERSION)
##  and tagged and pushed to:
##  ${CI_REGISTRY}/${CI_PROJECT_NAMESPACE}/${CI_PROJECT_NAME}/$(OCI_IMAGE):$(VERSION)

oci-publish: oci-pre-publish oci-do-publish oci-post-publish  ## publish the OCI_IMAGE to the CAR_OCI_REGISTRY_HOST registry from CI_REGISTRY

oci-pre-publish-all:

oci-post-publish-all:

## TARGET: oci-publish-all
## SYNOPSIS: make oci-publish-all
## HOOKS: oci-pre-publish-all, oci-post-publish-all
## VARS:
##       OCI_IMAGES_TO_PUBLISH=<image directories under ./images/> is the list of names of the images to publish
##       CAR_OCI_REGISTRY_HOST=<defaults to artefact.skao.int>
##       OCI_BUILDER=[docker|podman] - OCI executor for publishing images
##       OCI_SKIP_PUSH=<set non-empty to skip push after build>
##
##  Publish images listed in OCI_IMAGES_TO_PUBLISH to the CAR_OCI_REGISTRY_HOST by
##  iteratively calling oci-publish - see above.

oci-do-publish-all:
	$(foreach ociimage,$(OCI_IMAGES_TO_PUBLISH), make oci-publish OCI_IMAGE=$(ociimage); rc=$$?; if [[ $$rc -ne 0 ]]; then exit $$rc; fi;)

oci-publish-all: oci-pre-publish-all oci-do-publish-all oci-post-publish-all ## Publish all OCI Images in OCI_IMAGES_TO_PUBLISH

oci-pre-scan:

oci-post-scan:

oci-do-scan: VERSION := $(shell . $(RELEASE_SUPPORT) ; RELEASE_CONTEXT_DIR=$(RELEASE_CONTEXT_DIR) setContextHelper; getVersion)
oci-do-scan:
	@. $(OCI_SUPPORT) ; \
	export OCI_NEXUS_REPO=$(OCI_NEXUS_REPO); \
	echo "oci-do-scan: Checking for $(OCI_IMAGE) $(VERSION)"; \
	ociImageScan "$(OCI_IMAGE)" "$(VERSION)"; \
	echo "oci-do-scan: Image scan returned: $$ocis_result"; \
	if [[ "$$ocis_result" == "0" ]]; then \
		echo "oci-scan:OK: $(CAR_OCI_REGISTRY_HOST)/$(OCI_IMAGE):$(VERSION) "; \
		exit 0; \
	else \
		echo "oci-do-scan: ERROR $(CAR_OCI_REGISTRY_HOST)/$(OCI_IMAGE):$(VERSION)"; \
		exit 1; \
	fi

## TARGET: oci-scan
## SYNOPSIS: make oci-scan
## HOOKS: oci-pre-scan, oci-post-scan
## VARS:
##       OCI_IMAGE=<image name> is the image to be scanned by Trivy
##       CAR_OCI_REGISTRY_HOST=<defaults to artefact.skao.int> - registry where image held
##       VERSION=<semver tag of image> - defaults to release key in .release file
##       RELEASE_CONTEXT=<directory holding .release file>
##
##  Scan image OCI_IMAGE using Trivy.
##  iteratively calling oci-publish - see above.

oci-scan: oci-pre-scan oci-do-scan oci-post-scan  ## scan the OCI_IMAGE (must run inside docker.io/aquasec/trivy:latest)

oci-pre-scan-all:

oci-post-scan-all:

oci-do-scan-all:
	$(foreach ociimage,$(OCI_IMAGES_TO_PUBLISH), make oci-scan OCI_IMAGE=$(ociimage); rc=$$?; if [[ $$rc -ne 0 ]]; then exit $$rc; fi;)

## TARGET: oci-scan-all
## SYNOPSIS: make oci-scan-all
## HOOKS: oci-pre-scan-all, oci-post-scan-all
## VARS:
##       OCI_IMAGES_TO_PUBLISH=<image directories under ./images/> is the list of names of the images to be scanned by Trivy
##       CAR_OCI_REGISTRY_HOST=<defaults to artefact.skao.int> - registry where image held
##
##  Scan image OCI_IMAGE using Trivy.
##  iteratively calling oci-publish - see above.

oci-scan-all: oci-pre-scan-all oci-do-scan-all oci-post-scan-all ## Scan all OCI Images in OCI_IMAGES_TO_PUBLISH (must run inside docker.io/aquasec/trivy:latest)

## TARGET: oci-boot-into-tools
## SYNOPSIS: make oci-boot-into-tools
## HOOKS: none
## VARS:
##       OCI_BUILDER=[docker|podman] - OCI container executor
##       OCI_TOOLS_IMAGE=<OCI Tools Image> - tools image - default artefact.skao.int/ska-tango-images-pytango-builder
##
##  Launch the tools image with the current directory mounted at /app in container and
##  install the current requirements.txt .

oci-boot-into-tools: ## Boot the pytango-builder image with the project directory mounted to /app
	$(OCI_BUILDER) run --rm -ti --volume $(pwd):/app $(OCI_TOOLS_IMAGE) bash -c \
	'pip3 install black pylint-junit; if [[ -f "requirements-dev.txt" ]]; then pip3 install -r requirements-dev.txt; else if [[ -f "requirements.txt" ]]; then pip3 install -r requirements.txt; fi; fi; bash'

# end of switch to suppress targets for help
endif
endif
