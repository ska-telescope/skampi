#!/bin/bash
set -e
echo -e "section_start:`date +%s`:$1[collapsed=true]\r\e[0K$2"
${@:3}
echo -e "section_end:`date +%s`:$1\r\e[0K"
