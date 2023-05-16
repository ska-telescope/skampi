# include Makefile for help related targets and variables
# default target - generate help based on targets and vars

.DEFAULT_GOAL := help

# grab any additional targets
HELP_TARGET_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

## TARGET: help
## SYNOPSIS: make help <section name eg. oci>
## HOOKS: none
## VARS: none
##  show the short help description of each target in all the Makefiles
##  and show the public variable list.

HELP_CURRENT_TARGET := $(firstword $(MAKECMDGOALS))
ifeq ($(strip $(MAKECMDGOALS)),)
# then it will be the .DEFAULT_GOAL
HELP_CURRENT_TARGET := help
endif


# Colour bank https://stackoverflow.com/questions/4332478/read-the-current-text-color-in-a-xterm/4332530#4332530
# test that the terminal is functioning correctly
TEST_TERMINAL:=$(shell tput setaf 1 1>/dev/null 2>/dev/null && echo "YES")
ifeq ($(strip $(TEST_TERMINAL)),YES)
HELP_RED:=$(shell tput setaf 1 2>/dev/null || "")
HELP_GREEN:=$(shell tput setaf 2 2>/dev/null || "")
HELP_YELLOW:=$(shell tput setaf 3 2>/dev/null || "")
HELP_LIME_YELLOW:=$(shell tput setaf 190 2>/dev/null || "")
HELP_POWDER_BLUE:=$(shell tput setaf 153 2>/dev/null || "")
HELP_BLUE:=$(shell tput setaf 4 2>/dev/null || "")
HELP_NORMAL:=$(shell tput sgr0 2>/dev/null || "")
endif

# hide help in here so that it does not get redefined above
ifeq (help,$(HELP_CURRENT_TARGET))

# if a local help has been defined then skip this one
ifndef HELP_DEFINED

# suppress additional targets
ifneq ($(strip $(HELP_TARGET_ARGS)),)
$(eval $(HELP_TARGET_ARGS):;@:)
endif

# Check if makefile repository needs an update
ifneq ($(shell git log -n 1 --format="%H"),$(shell git ls-remote https://gitlab.com/ska-telescope/sdi/ska-cicd-makefile.git HEAD --format=%H | awk '{print $1};'))
$(info $(HELP_LIME_YELLOW)There's a new makefile submodule update, please run 'make make' to update!$(HELP_NORMAL))
endif

# This target finds all the ## documented targets through introspection of the
# built-in MAKEFILE_LIST.  It also enables the user to select a section using the 2nd argument (target)
# 1. iterate Makefiles (as a section)
# 2. check whether the section matches the additional target args or is absent
# 3. grep the file for ## docs for targets and variables
# 4. format and print
#  The section list is pruned to remove the parent Makefile, and trimmed of the
#  file prefix and suffix (prefix can exist for Makefile run in ./tests)
#  The formating uses awk to inject terminal colurs, and to align keywords
help: ## show this help.
	@for mkfile in $(MAKEFILE_LIST); do \
		section=`echo $$mkfile | sed 's/\.\.\///g' | sed 's/^\.make\///g' | sed 's/\.mk//g'`; \
		if [[ "$$section" != "base" ]] && [[ "$$section" != "PrivateRules.mak" ]]; then \
			if [[ "" == "$(HELP_TARGET_ARGS)" ]] || [[ $$( echo $$section | grep "$(HELP_TARGET_ARGS)" ) ]]; then \
				echo ""; echo "------"; \
				echo "$(HELP_POWDER_BLUE)SECTION:$(HELP_NORMAL) $$section"; \
				echo "$(HELP_GREEN)MAKE TARGETS:$(HELP_NORMAL)"; \
				grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $$mkfile | sed 's/^\.\.\///' | sed 's/^\.make\///' | sort | awk 'BEGIN {FS = ": .*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'; \
				echo ""; echo "$(HELP_YELLOW)MAKE VARS (+defaults):$(HELP_NORMAL)"; \
				grep -E '^[0-9a-zA-Z_-]+ \?=.*$$' $$mkfile | sed 's/^\.\.\///' | sed 's/^\.make\///' | sort | awk 'BEGIN {FS = " \\?= "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' || true ; \
			fi; \
		fi; \
	done

.PHONY: help
endif
endif

## TARGET: long-help
## SYNOPSIS: make long-help <section name eg. oci>
## HOOKS: none
## VARS: none
##  show the long help description of targets in a selected Makefile section
##  or all of them.

# This target finds all the ## documented targets through introspection of the
# built-in MAKEFILE_LIST.  It also enables the user to select a section using the 2nd argument (target)
# or failing that, they are prompted for a section
# 1. ask for a section from an offered list
# 2. iterate Makefiles (as a section)
# 3. check whether the section matches the additional target args or is absent
# 4. grep the file for ## docs for targets and variables
# 5. format and print
#  The section list is pruned to remove the parent Makefile, and trimmed of the
#  file prefix and suffix (prefix can exist for Makefile run in ./tests)
#  The formating uses awk to inject terminal colurs, and to align keywords

ifeq (long-help,$(firstword $(MAKECMDGOALS)))
# suppress additional targets
ifneq ($(strip $(HELP_TARGET_ARGS)),)
$(eval $(HELP_TARGET_ARGS):;@:)
endif

  # use the rest as arguments for "long-help"
  # ...and turn them into do-nothing targets

long-help: ## show detailed help.
	@sections=`echo $(MAKEFILE_LIST) | sed 's/base//' | sed 's/Makefile//' | sed 's/\.\.\///g' | sed 's/^\.make\///g' | sed 's/\.mk//g'`; \
	if [[ "" == "$(HELP_TARGET_ARGS)" ]]; then \
		read -p "$(HELP_POWDER_BLUE)Enter a Makefile section name or press enter for all $(HELP_NORMAL) 🔎 $(HELP_YELLOW)[$$sections]$(HELP_NORMAL): " HELP_SECTION; \
	else \
		HELP_SECTION="$(HELP_TARGET_ARGS)"; \
	fi; \
	if [[ "" == $$( echo $$sections | grep $${HELP_SECTION} ) ]]; then \
		echo "$(HELP_RED)❗Invalid Selection: $${HELP_SECTION}$(HELP_NORMAL)"; \
		echo "Please enter a valid section: $(HELP_YELLOW)[$$sections]$(HELP_NORMAL)"; \
		exit 0; \
	fi; \
	for section in $(MAKEFILE_LIST); do \
		if [[ "" == "$${HELP_SECTION}" ]] || [[ $$( echo $$section | grep $${HELP_SECTION} ) ]]; then \
		grep -E '^##.*$$' $$section | \
		sed 's/^\#\# \?//' | \
		awk 'BEGIN {FS = ":"}; {printf "%9-s%s\n", $$1":", $$2}' | \
		sed 's/\: *$$//' | \
		sed -r 's/^(TARGET:)(.*)$$/\n$(HELP_POWDER_BLUE)-------$(HELP_NORMAL)\n$(HELP_GREEN)\1$(HELP_NORMAL)\2/' | \
		sed -r 's/^(VARS:)(.*)$$/$(HELP_YELLOW)\1$(HELP_NORMAL)\2/' | \
		sed -r 's/^(VARS)$$/$(HELP_YELLOW)\1:$(HELP_NORMAL)/' | \
		sed -r 's/^(HOOKS:)(.*)$$/$(HELP_POWDER_BLUE)\1$(HELP_NORMAL)\2/' | \
		sed -r 's/^(SYNOPSIS:)(.*)$$/$(HELP_POWDER_BLUE)\1$(HELP_NORMAL)\2/' | \
		sed -r 's/^(NOTE)( .*)$$/$(HELP_YELLOW)❗\1:$(HELP_NORMAL)\2/' \
		; \
		fi; \
	done

.PHONY: long-help
endif

help-test-colours: ## Private target: print the test colours
	echo "$(HELP_RED)HELP_RED$(HELP_NORMAL)"
	echo "$(HELP_GREEN)HELP_GREEN$(HELP_NORMAL)"
	echo "$(HELP_YELLOW)HELP_YELLOW$(HELP_NORMAL)"
	echo "$(HELP_LIME_YELLOW)HELP_LIME_YELLOW$(HELP_NORMAL)"
	echo "$(HELP_POWDER_BLUE)HELP_POWDER_BLUE$(HELP_NORMAL)"
	echo "$(HELP_BLUE)HELP_BLUE$(HELP_NORMAL)"
	echo "$(HELP_NORMAL)HELP_NORMAL$(HELP_NORMAL)"

.PHONY: help-test-colours

help-print-targets: ## Private target: print the current Makefile context targets
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ": .*?## "}; {p=index($$1,":")} {printf "\033[36m%-30s\033[0m %s\n", substr($$1,p+1), $$2}';

.PHONY: help-print-targets

