#!/bin/bash
python3 -m pip install atlassian-python-api
cd tests/resources/utils/chart_imager/
python3 confluence_chart_uploader.py