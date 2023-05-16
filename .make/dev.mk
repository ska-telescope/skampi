# include Makefile for developer tools related targets and variables

MAKE_GIT_HOOKS_DIR := resources/git-hooks/
MAKE_VSCODE_CONFIG_DIR := resources/vscode

# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

.PHONY: dev-git-hooks dev-vscode

## TARGET: dev-git-hooks
## SYNOPSIS: make dev-git-hooks
## HOOKS: none
## VARS: none
##  activate git-hooks if available in this project.

dev-git-hooks:  ## activate git-hooks if available in project
	@if [[ -d "$(MAKE_GIT_HOOKS_DIR)" ]]; then \
		echo "dev-git-hooks: enabling hooks in $(MAKE_GIT_HOOKS_DIR): $$(ls $(MAKE_GIT_HOOKS_DIR))"; \
		git config --local core.hooksPath  $(MAKE_GIT_HOOKS_DIR); \
	else \
		echo "dev-git-hooks: no hooks found in $(MAKE_GIT_HOOKS_DIR)"; \
	fi

## TARGET: dev-vscode
## SYNOPSIS: make dev-vscode
## HOOKS: none
## VARS: none
##  Setup/copy vscode and devcontainer config if available in this project.

dev-vscode:  ## copy in vscode config if available in project
	@repository_dir=$$(git rev-parse --show-toplevel); \
	if [[ -d "$(MAKE_VSCODE_CONFIG_DIR)/vscode" ]] || [[ -d "$(MAKE_VSCODE_CONFIG_DIR)/devcontainer" ]]; then \
		if [[ -d "$(MAKE_VSCODE_CONFIG_DIR)/vscode" ]]; then \
		 	echo "$(MAKE_VSCODE_CONFIG_DIR)/vscode exists"; \
			mkdir -p $${repository_dir}/.vscode; \
			cp -r $(MAKE_VSCODE_CONFIG_DIR)/vscode/ $${repository_dir}/.vscode/; \
			echo "dev-vscode: added vscode config"; \
		fi; \
		if [[ -d "$(MAKE_VSCODE_CONFIG_DIR)/devcontainer" ]]; then \
		 	echo "$(MAKE_VSCODE_CONFIG_DIR)/devcontainer exists"; \
			mkdir -p $${repository_dir}/.devcontainer; \
			cp -R $(MAKE_VSCODE_CONFIG_DIR)/devcontainer/* $${repository_dir}/.devcontainer/; \
			echo "dev-vscode: added devcontainer config"; \
		fi; \
		echo "dev-vscode: enabled vscode config from $(MAKE_VSCODE_CONFIG_DIR) - you may need to restart your vscode for this to take effect"; \
	else \
		echo "dev-vscode: no vscode config found in $(MAKE_VSCODE_CONFIG_DIR)"; \
	fi

# end of switch to suppress targets for help
endif
endif
