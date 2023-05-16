# include Makefile for make related targets and variables

# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

.PHONY: make submodule

## TARGET: make
## SYNOPSIS: make make
## HOOKS: none
## VARS: none
##  update the .make submodule containing the common Makefile targets and variables.


ifneq (long-help,$(firstword $(MAKECMDGOALS)))
make:  ## Update the .make git submodule
	cd .make && git checkout master
	cd .make && git fetch
	git submodule update --remote --merge
endif

## TARGET: submodule
## SYNOPSIS: make submodule
## HOOKS: none
## VARS: none
##  Force initialisation and update of all git submodules in this project.

submodule:  ## update git submodules
	git submodule init
	git submodule update --recursive --remote
	git submodule update --init --recursive

# end of switch to suppress targets for help
endif
endif
