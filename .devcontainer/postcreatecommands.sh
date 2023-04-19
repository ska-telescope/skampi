#!/bin/bash

# SET POETRY TO CREATE VIRTUALENVIRONMENTS
poetry config virtualenvs.in-project true

# INSTALL SSH CLIENT
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install openssh-client -y

echo "If you are running this under linux, and you want to use SSH from your devcontainer, you should run .devcontainer/runlocalagent.sh in your local host in a separate shell."