#!/bin/bash
# Usage: bash resources/gitlab_section.sh <label> "<Command Description>" <command>
# Example: bash resources/gitlab_section.sh current_time "Show the current time" date
echo -e "section_start:`date +%s`:$1[collapsed=true]\r\e[0K$2"
${@:3}
echo -e "section_end:`date +%s`:$1\r\e[0K"
