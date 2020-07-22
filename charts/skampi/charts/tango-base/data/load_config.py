# coding: utf-8
"""Loads test Configuration JSON objects.

- SDP Configure JSON as: `sdp_config`
- CSP ConfigureScan JSON as: `csp_scan_config`

Load into iTango with:

    %run scripts/load_config.py

"""
import json
from os.path import join

with open(join('data', 'sdp-subarray-configure-0001.json')) as file:
    sdp_config = json.dumps(json.loads(file.read()))

with open(join('data', 'csp-subarray-configure-scan-0001.json')) as file:
    csp_scan_config = json.dumps(json.loads(file.read()))
