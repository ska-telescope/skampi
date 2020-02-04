"""
This file runs an 'observation' by loading Configuration Data Model
instances from a file and using them to configure a Sub-Array.

This script assumes the telescope is in standby and that all
resources are unallocated.
"""
import csv
import sys

import oet.domain as domain

if len(sys.argv) != 2:
    print('Usage: scanrunner <name of CSV file>')
    print('\ne.g., scanrunner scan_definitions.csv')
    sys.exit(0)

scan_sequence_file = sys.argv[1]

subarray = domain.SubArray(1)

print('Reading scan sequence from {}'.format(scan_sequence_file))
with open(scan_sequence_file, 'r') as csv_file:

    for row in csv.reader(csv_file, delimiter=','):
        exported_cdm, scan_duration = row

        print('Configuring sub-array {} using CDM from {}'.format(subarray.id, exported_cdm))
        subarray.configure_from_file(exported_cdm)

        print('Scanning for {} seconds'.format(scan_duration))
        subarray.scan(float(scan_duration))

    subarray.end_sb()
