#/bin/env python3
"""
Analyse results from many stress-test runs into a report

Usage:
  make_analysis.py [<eval>...] [--matches-per-clfr=<N>] [--context-lines=<N>]
     [--gitlab=<uri>] [--gitlab-header=<k=v>] [--gitlab-project=<id>]
     [--gitlab-search=<k=v>] [--gitlab-job=<name>] [--gitlab-artifact=<name>]

Options:
  <eval>                   Path/URIs of log files (possibly in tarballs)
  --matches-per-clfr=<N>   How many matches to report per classifier (default 3)
  --context-lines=<N>      Log lines to show for context around match (default 30)
  --gitlab=<uri>           Gitlab instance to query
  --gitlab-header=<k=v>    Parameters to GitLab API (e.g. private_token=...)
  --gitlab-project=<name>  Project ID to query (e.g. ska-telescope/skampi)
  --gitlab-search=<k=v>    Pipeline search parameters (e.g. user=...)
  --gitlab-job=<name>      Job to locate
  --gitlab-artifact=<name> Artefact to download
"""

from docopt import docopt
import sys
import os
import rstgen
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis import logs, tests, classifiers
from analysis.report import Report

arguments = docopt(__doc__, version='SKAMPI log analysis')

matches_per_clfr_count = int(arguments['--matches-per-clfr'] or 3)
context_lines = int(arguments['--context-lines'] or 30)

# Collected data
report = Report(matches_per_clfr_count, context_lines)

# Read from GitLab
if arguments['--gitlab'] is not None:

    if arguments['--gitlab-project'] is None or arguments['--gitlab-job'] is None \
       or arguments['--gitlab-artifact'] is None:
        print("Please specify GitLab project, job and artefact!")
        exit(1)

    def split_map(s):
        # Split first by '&', then into key=value pairs
        return { k: v for k,v in [ kv.split('=') for kv in s.split('&') if kv ] }

    report.add_from_gitlab(
        arguments['--gitlab'],
        split_map(arguments['--gitlab-header'] or ''),
        arguments['--gitlab-project'],
        split_map(arguments['--gitlab-search'] or ''),
        arguments['--gitlab-job'].split(','),
        arguments['--gitlab-artifact'])

# Read triggers from files
for fname in arguments['<eval>']:
    try:
        report.add_file_or_uri(fname)
    except Exception:
        traceback.print_exc()
report.build_maps()

# Create overview
pages = {
    'Overview': [ 'overview.rst', 'timing.rst' ],
    'Never': [], 'Always': [], 'Sometimes': []
}
with open("overview.rst", "w", encoding='utf-8') as f:

    print(rstgen.header(1, 'Test Overview'), file=f)
    print(f'{report.total_lines} lines scanned against {len(classifiers.classifiers)} '
          'classifiers, result summary:\n', file=f)
    report.make_overview_table(f)

    for rev,date in sorted(report.revisions.items(),
                           key = lambda rev_date: rev_date[1],
                           reverse = True):
        print(rstgen.header(2, rev), file=f)
        report.make_overview_table(f, rev)

# Create timing overview
with open("timing.rst", "w", encoding='utf-8') as f:

    print(rstgen.header(1, 'Timing Overview'), file=f)

    print("Average time of first message from every container and pod.\n", file=f)

    report.make_pod_timing_table(f)

# For every classifier, create report
for cfr in sorted(classifiers.classifiers, key=lambda cfr: cfr.skb):
    try:
        with open(cfr.skb + ".rst", "w", encoding='utf-8') as f:
            matches = report.make_cfr_report(f, cfr)
        if matches == 0:
            pages['Never'].append(cfr.skb + ".rst")
        elif matches >= 0.9:
            pages['Always'].append(cfr.skb + ".rst")
        else:
            pages['Sometimes'].append(cfr.skb + ".rst")
    except Exception:
        traceback.print_exc()

# Write raw log files
full_log_count = report.write_logs('.')

# Generate index
with open('index.rst', 'w', encoding='utf-8') as f:

    print(rstgen.header(1, "Test Report"), file=f)

    summary = f"Total {report.total_lines} lines scanned, {full_log_count} logs included in full."
    print(summary, file=f)

    for section in ['Overview', 'Always', 'Sometimes', 'Never']:
        print(rstgen.toctree(*pages[section], maxdepth=2, caption=section), file=f)

    print(summary)
