# include Makefile for docs (RTD) related targets and variables

# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

SHELL := /usr/bin/env bash
# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
DOCS_SPHINXOPTS    ?= ## docs Sphinx opts
DOCS_SPHINXBUILD   ?= python3 -msphinx ## Docs Sphinx build command
DOCS_SOURCEDIR     ?= docs/src ## docs sphinx source directory
DOCS_BUILDDIR      ?= docs/build ## docs sphinx build directory

ifeq (docs-build,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "docs-build"
  DOCS_TARGET_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(DOCS_TARGET_ARGS):;@:)
endif

ifeq (docs-help,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "docs-help"
  DOCS_TARGET_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(DOCS_TARGET_ARGS):;@:)
endif

# Put it first so that "make" without argument is like "make help".
docs-help:  ## help for docs
	@$(DOCS_SPHINXBUILD) -M help $(DOCS_SOURCEDIR) $(DOCS_BUILDDIR) $(DOCS_SPHINXOPTS) $(DOCS_TARGET_ARGS)

docs-pre-build:

docs-post-build:

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
docs-do-build:
	mkdir -p $(DOCS_BUILDDIR)
	$(DOCS_SPHINXBUILD) -M $(DOCS_TARGET_ARGS) $(DOCS_SOURCEDIR) $(DOCS_BUILDDIR) $(DOCS_SPHINXOPTS)

## TARGET: docs-build
## SYNOPSIS: make docs-build <sphinx command such as html|help|latex|clean|...>
## HOOKS: docs-pre-build, docs-post-build
## VARS:
##       DOCS_SOURCEDIR=<docs source directory> - default ./docs/src
##       DOCS_BUILDDIR=<docs build directory> - default ./docs/build
##       DOCS_SPHINXOPTS=<additional command line options for Sphinx>
##
##  Build the RST documentation in the ./docs directory.

docs-build: docs-pre-build docs-do-build docs-post-build  ## Build docs - must pass sub command

.PHONY: docs-help docs-pre-build docs-do-build docs-post-build docs-build

# end of switch to suppress targets for help
endif
endif
