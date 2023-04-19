#!/bin/bash
if [ -z "$SSH_AUTH_SOCK" ]; then
    echo "settiing up a new env var for SSH_AUTH_SOCK"
    # Check for a currently running instance of the agent
    RUNNING_AGENT="`ps -ax | grep 'ssh-agent -s' | grep -v grep | wc -l | tr -d '[:space:]'`"
    echo "currently running agent == "$RUNNING_AGENT
    if [ "$RUNNING_AGENT" = "0" ]; then
        echo "launching a new agent"
        # Launch a new instance of the agent
        ssh-agent -s &> $HOME/.ssh/ssh-agent
    fi
    eval `cat $HOME/.ssh/ssh-agent`
fi
