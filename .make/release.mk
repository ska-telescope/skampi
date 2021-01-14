#
#   Copyright 2015  Xebia Nederland B.V.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
ifeq ($(strip $(PROJECT)),)
  NAME=$(shell basename $(CURDIR))
else
  NAME=$(PROJECT)
endif

RELEASE_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-release-support

VERSION=$(shell . $(RELEASE_SUPPORT) ; getVersion)
TAG=$(shell . $(RELEASE_SUPPORT); getTag)
SHELL=/bin/bash

.PHONY: patch-release minor-release major-release tag check-status check-release showver \
	create-tag create-publish-tag push-tag config-git \
	release-skampi delete-tag release-skampi-if-no-error

.release:
	@echo "release=0.0.0" > .release
	@echo "tag=$(NAME)-0.0.0" >> .release
	@echo INFO: .release created
	@cat .release
	@echo DESCRIPTION

# release: check-status check-release build create-tag push

showver: .release
	@. $(RELEASE_SUPPORT); getVersion

bump-patch-release: VERSION := $(shell . $(RELEASE_SUPPORT); nextPatchLevel)
bump-patch-release: .release tag

bump-minor-release: VERSION := $(shell . $(RELEASE_SUPPORT); nextMinorLevel)
bump-minor-release: .release tag

bump-major-release: VERSION := $(shell . $(RELEASE_SUPPORT); nextMajorLevel)
bump-major-release: .release tag

patch-release: tag-patch-release release
	@echo $(VERSION)

minor-release: tag-minor-release release
	@echo $(VERSION)

major-release: tag-major-release release
	@echo $(VERSION)

tag: TAG=$(shell . $(RELEASE_SUPPORT); getTag $(VERSION))
tag: check-status
#	@. $(RELEASE_SUPPORT) ; ! tagExists $(TAG) || (echo "ERROR: tag $(TAG) for version $(VERSION) already tagged in git" >&2 && exit 1) ;
	@. $(RELEASE_SUPPORT) ; setRelease $(VERSION)
#	git add .
#	git commit -m "bumped to version $(VERSION)" ;
#	git tag $(TAG) ;
#	@ if [ -n "$(shell git remote -v)" ] ; then git push --tags ; else echo 'no remote to push tags to' ; fi

check-versions:
	@. $(RELEASE_SUPPORT) ; ! hasChanges || (echo "ERROR: there are still outstanding changes" >&2 && exit 1) ;

check-release: .release
	@. $(RELEASE_SUPPORT) ; tagExists $(TAG) || (echo "ERROR: version not yet tagged in git. make [minor,major,patch]-release." >&2 && exit 1) ;
	@. $(RELEASE_SUPPORT) ; ! differsFromRelease $(TAG) || (echo "ERROR: current directory differs from tagged $(TAG). make [minor,major,patch]-release." ; exit 1)

create-tag: .release
	@. $(RELEASE_SUPPORT) ; createGitTag || (echo "ERROR: Some error in creating tag" >&2 && exit 1) ;

push-tag: .release
	@. $(RELEASE_SUPPORT) ; gitPush $$USERNAME

create-publish-tag: create-tag push-tag

config-git:
	echo "USERNAME = $$USERNAME"
	echo "EMAILID = $$EMAILID"
	git config --global user.email "$(EMAILID)"
	git config --global user.name "$(USERNAME)"

release-skampi: config-git create-publish-tag release-skampi-if-no-error

delete-tag: .release
	@. $(RELEASE_SUPPORT) ; deleteTag

release-skampi-if-no-error: .release
	@. $(RELEASE_SUPPORT) ; releaseSKAMPIIfNoError $$USERNAME
