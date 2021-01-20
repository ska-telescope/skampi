#/bin/env python3
"""
Kubernetes log collection script

Usage:
  collect_k8s_logs.py <ns>... [--timefmt=<format>]
      [--pp=<out>] [--dump=<out>] [--tests=<out>] [--test=<test>]

Options:
  <ns>           Namespaces or JSON dump files (files must have '/' or '.')
  --timefmt=<fmt>  Format timestamps (default %H:%M:%S.%f)
  --pp=<out>     Pretty-print to file ('-' for stdout - default)
  --dump=<out>   Write JSON strings to file ('-' for stdout)
  --tests=<out>  Put test case summary into file ('-' for stdout)
  --test=<test>  Filter out only test of given name
"""

from kubernetes import client, config

import datetime
from datetime import timedelta, timezone
import sys
import re
import json
from docopt import docopt


# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()
v1 = client.CoreV1Api()

# Regular expressions
kube_time_re = re.compile('^(?P<kube_time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{0,6})\d*Z (?P<rest>.*)')
ska_re = re.compile('^1\|(?P<ska_time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d*Z)\|(?P<ska_level>[^\|]*)\|(?P<ska_thread>[^\|]*)\|(?P<ska_function>[^\|]*)\|(?P<ska_source>[^\|]*)\|(?P<ska_tags>[^\|]*)\|(?P<msg>.*)$')

# Standard datetime parsing tools
def parse_date(date):
    dt = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f')
    return dt.replace(tzinfo=timezone.utc)

def render_date(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')

SAME_ATTRS_THRESHOLD = datetime.timedelta(milliseconds=0.1)
def parse_log_line(line :str, attrs :dict, previous :dict) -> dict:

    out = dict(attrs)

    # Parse Kubernetes timestamp
    m = kube_time_re.match(line)
    if not m:
        print('could not parse K8s timestamp: ', line)
    else:
        out['time'] = parse_date(m['kube_time'])
        line = m['rest']

    # Attempt to parse SKA format
    m = ska_re.match(line)
    if m:
        out['ska_time'] = m['ska_time']
        out['level'] = m['ska_level']
        out['thread'] = m['ska_thread']
        out['function'] = m['ska_function']
        out['source'] = m['ska_source']
        out['tags'] = {
            name_val[0] : name_val[1] if len(name_val) > 1 else None
            for name_val in
            [ tag.split(':') for tag in m['ska_tags'].split(',') ]
        }
        line = m['msg']

    # If a line without SKA-specific annotations follows one with
    # them, assume that we are simply dealing with a log message that
    # included '\n', which have now been split over multiple lines
    elif 'ska_time' in previous and \
         out.get('time') - previous.get('time') < SAME_ATTRS_THRESHOLD:
        out['ska_time'] = previous['ska_time']
        out['level'] = previous['level']
        out['thread'] = previous['thread']
        out['function'] = previous['function']
        out['source'] = previous['source']
        out['tags'] = previous['tags']

    out['msg'] = line
    return out

def aggregate_status(dct, statuses):
    """ Small helper for counting appearing levels """

    if 'level' in dct:
        if dct['level'] not in statuses:
            statuses[dct['level']] = 1
        else:
            statuses[dct['level']] += 1

def collect_pod_logs(namespace):
    ret = v1.list_namespaced_pod(namespace, watch=False)
    lines = []
    print(f"Obtaining logs from {len(ret.items)} pods on namespace {namespace}...")
    for pod in ret.items:

        podName = pod.metadata.name

        # Collect containers
        containers = []
        if pod.spec.init_containers is not None:
            containers += pod.spec.init_containers
        if pod.spec.containers is not None:
            containers += pod.spec.containers

        # Loop through them to collect logs
        statuses = {}
        for container in containers:
            containerName = container.name

            for previous in [True, False]:
                try:
                    logs = v1.read_namespaced_pod_log(podName, namespace,
                                                      previous=previous,
                                                      container=containerName,
                                                      timestamps=True)
                except client.rest.ApiException as e:

                    # Try to parse as JSON to figure out whether
                    # something strange happened. As we are
                    # speculatively asking for previous containers,
                    # 'not found' errors are quite expected
                    body = json.loads(e.body)
                    if not body['message'].endswith('not found'):
                        print(f'While querying logs for pod {podName} container {containerName}: {e}')
                    continue
                attrs = { 'pod': podName, 'container': containerName,
                          'previous': previous, 'namespace': namespace }
                line_dict = {}
                for line in logs.split('\n'):
                    if len(line) > 0:

                        # Add line to list
                        line_dict = parse_log_line(line, attrs, line_dict)
                        lines.append(line_dict)
                        aggregate_status(line_dict, statuses)

        if 'ERROR' in statuses or 'CRITICAL' in statuses:
            print(f'  {podName}:', ', '.join(
                [f'{n}x{level}' for level,n in statuses.items()]))

    print(f'  ... {len(lines)} lines read')
    return lines


def collect_events(namespace):

    print(f"Obtaining events from namespace {namespace}...")
    lines = []
    api_response = v1.list_namespaced_event(namespace, watch=False)
    cont_re = re.compile('^spec.containers{(?P<container>.*)}$')

    statuses = {}
    for item in api_response.items:
        if item.first_timestamp is not None:

            # Get attributes
            attrs = {'msg': item.message, 'level': item.type }
            attrs[item.involved_object.kind.lower()] = item.involved_object.name
            attrs['namespace'] = item.involved_object.namespace
            if item.involved_object.field_path is not None:
                m = cont_re.match(item.involved_object.field_path)
                if m:
                    attrs['container'] = m['container']

            # Generate line for first time stamp
            date_format = '%Y-%m-%d %H:%M:%S'
            lines.append({'time': item.first_timestamp, **attrs})
            aggregate_status(attrs, statuses)

            # Generate line for last time stamp
            if (item.last_timestamp - item.first_timestamp).total_seconds() != 0:
                lines.append({'time': item.last_timestamp, **attrs})
                aggregate_status(attrs, statuses)

    print(f'  ... {len(lines)} events:', ', '.join(
                [f'{n}x{level}' for level,n in statuses.items()]))

    return lines

def collect_file(filename):

    print(f"Reading from {filename}...")
    # Read JSON lines from a file
    lines = []
    with open(filename, 'r') as f:
        for line in f:
            line_dict = json.loads(line)
            if 'time' in line_dict:
                line_dict['time'] = parse_date(line_dict['time'])
            lines.append(line_dict)

    print(f"  ... {len(lines)} lines read")
    return lines

# Collect lines
arguments = docopt(__doc__, version='Naval Fate 2.0')

lines = []
for namespace in arguments['<ns>']:
    if '.' in namespace or '/' in namespace:
        lines += collect_file(namespace)
    else:
        lines += collect_pod_logs(namespace)
        lines += collect_events(namespace)
lines = sorted(lines, key = lambda line: line['time'])

# Default is pretty-print to stdout
pp_target = arguments['--pp']
dump_target = arguments['--dump']
tests_target = arguments['--tests']
if pp_target is None and dump_target is None and tests_target is None:
    pp_target = '-'

# Small helper for printing to stdout/file
def make_target(target_name, message=''):
    if target_name is not None:
        if target_name == '-':
            yield sys.stdout
        else:
            print(message)
            with open(target_name, 'w', encoding='utf-8') as f:
                yield f

# Pretty-print
pp_date_format = arguments['--timefmt']
if pp_date_format is None:
    pp_date_format = '%H:%M:%S.%f'
def pp_line(line):
    return f"{line['time'].strftime(pp_date_format)} {line.get('level', '---')}\t{line.get('pod', '---')}:{line.get('container', '---')}\t{line['msg']}"
for pp_file in make_target(pp_target, f'Pretty-printing to {pp_target}...'):
    for line in lines:
        print(pp_line(line), file=pp_file)

# Dump
for dump_file in make_target(dump_target, f'Dumping JSON to {dump_target}...'):
    for line in lines:
        print(json.dumps( { **line, 'time': render_date(line['time']) }),
              file=dump_file)

def collect_tests(lines):
    """ Collect and reorganise pytest results """

    tests = []
    test_start_re = re.compile('(?P<file>tests/[\w\d/_\-\.]+\.py)\:\:(?P<name>[\w\d/_\-\.]+)(?P<param>\[[^\]]*\])?')
    test_end_re = re.compile('(?P<status>[A-Z]+) +\[[ ]*\d+\%\]$')
    test_teardown_re = re.compile('\-+\ [\w ]+ \-+')
    test_error_report_re = re.compile('=+ [A-Z]+ =+')

    def is_test_runner(line):
        # Filter out lines from non-makefile-runner pods
        return 'pod' in line and 'makefile-runner' in line['pod']

    # Go forward to session start (ignore initialisation)
    session_start_re = re.compile('=+ test session starts =+')
    i = 0
    while i < len(lines):
        if is_test_runner(lines[i]) and session_start_re.match(lines[i]['msg']):
            break
        i += 1;
    i += 1;

    # First phase: Collect main test output
    start_line = i
    skipped = 0
    while i < len(lines):
        line = lines[i]
        if not is_test_runner(line):
            i += 1; skipped += 1
            continue
        if test_error_report_re.match(line['msg']):
            i += 1; skipped += 1
            break

        # Start of test?
        m = test_start_re.match(line['msg'])
        if not m:
            i += 1; skipped += 1
            continue
        test = {
            'file': m['file'],
            'name': m['name']
        }
        if m['param'] is not None:
            test['param'] = m['param']
        tests.append(test)

        # Get all lines before the first test runner line that are not
        # from the test runner itself - Python waits with generating
        # the line until the test has possibly finished, so relevant
        # logs often appear *before* this line.
        while i > 0:
            if is_test_runner(lines[i-1]):
                # An empty line generally marks the beginning of the test
                if not lines[i-1]['msg']:
                    break
                # Otherwise stop on the last test case end (i.e. make
                # sure we do not drop any lines!)
                if test_end_re.search(lines[i-1]['msg']):
                    break
            i -= 1

        # Now add log lines until we hit the end
        test_lines = []
        while i < len(lines):
            test_lines.append(lines[i])
            # Test ended?
            if is_test_runner(lines[i]):
                m = test_end_re.search(lines[i]['msg'])
                if m:
                    test['status'] = m['status']
                    break
            i += 1
        i += 1
        test['msgs'] = test_lines

        # Add further lines if there's a teardown (up to an empty line)
        if i < len(lines) and is_test_runner(lines[i]) and \
           test_teardown_re.match(lines[i]['msg']):

            teardown_lines = []
            while i < len(lines) and lines[i]['msg']:
                teardown_lines.append(lines[i])
                i += 1

            # Except if the teardown failed, which will be indicated
            # by an empty line followed by a 'FAILED' for the
            # test. Those two lines we also want.
            failed_teardown_prefix = test['file']+'::'+test['name']+' '
            if i+1 < len(lines) and lines[i+1]['msg'].startswith(failed_teardown_prefix):
                teardown_lines.append(lines[i])
                teardown_lines.append(lines[i+1])
                m = test_end_re.search(lines[i+1]['msg'])
                if m:
                    test['teardown_status'] = m['status']
                i+=2

            test['teardown'] = teardown_lines

    # Second phase: Detailed error reports. We get the reports in the
    # same order, which is a god-send because the names are often not
    # unique. Keep track of which ones we haven't visited yet.
    unmatched_tests = list(tests)
    report_start_re = re.compile('_+ (?P<status>[A-Z]+ at (?P<occasion>\w+) of )?(?P<name>[\w\d_]+)(?P<param>\[[^\]]*\])? _+$')
    section_start_re = re.compile('\-+ (?P<title>[\w ]+) \-+$')
    end_re = re.compile('=+ [ a-z]+ summary [ a-z]+ =+')
    while i < len(lines):
        line = lines[i]
        if not is_test_runner(line):
            i += 1; skipped += 1
            continue
        if end_re.match(lines[i]['msg']):
            break

        # New reports group?
        if test_error_report_re.match(lines[i]['msg']):
            i += 1; skipped += 1
            unmatched_tests = list(tests) # Tests might appear again!
            continue

        # Must match a report start
        m = report_start_re.match(line['msg'])
        if not m:
            i += 1; skipped += 1
            continue

        # Find test
        while unmatched_tests and \
              (unmatched_tests[0]['name'] != m['name'] or \
               unmatched_tests[0].get('param') != m['param']):
            unmatched_tests.pop(0)
        if not unmatched_tests:
            print(f"Could not match test {m['name']} {m['param']}! Discarding data!")
            i += 1; skipped += 1
            continue
        test = unmatched_tests.pop(0)
        occasion = m['occasion']

        sections = {}
        current_section = 'main'
        current_lines = [lines[i]]
        i += 1

        # Get lines
        while i < len(lines):
            if not is_test_runner(line):
                i += 1; skipped += 1
                continue

            # New report?
            if report_start_re.match(lines[i]['msg']) or \
               test_error_report_re.match(lines[i]['msg']) or \
               end_re.match(lines[i]['msg']):
                break

            # New section?
            m = section_start_re.match(lines[i]['msg'])
            if m:
                sections[current_section] = current_lines
                current_section = m['title']
                current_lines = sections.get('current_section', [])

                current_lines.append(lines[i])
                i += 1
                continue
            current_lines.append(lines[i])
            i+= 1

        # Complete reports
        sections[current_section] = current_lines
        test['detail' if occasion is None else occasion+'_detail'] = sections

    skipped += len(lines) - i
    print(f'Finished, {len(lines)-skipped-start_line}/{len(lines)-start_line} lines of test report used')
    return tests

# Find test cases
for tests_file in make_target(tests_target, f'Writing test report to {tests_target}...'):

    # Done, print results
    for test in collect_tests(lines):
        if arguments['--test'] is not None:
            if test['name'] != arguments['--test']:
                continue
        print('\n===', test['status'], test['file'], test['name'], test.get('param', ''), '===',
              file=tests_file)

        # Show test case report + detail
        for tl in test['msgs']:
           print(pp_line(tl), file=tests_file)
        for section_name, section_lines in test.get('detail', {}).items():
            print(f' # {section_name}:', file=tests_file)
            for sct_line in section_lines:
                print(' ', sct_line['msg'], file=tests_file)

        # Teardown report?
        if 'teardown' not in test:
            continue
        print('--- teardown ---', file=tests_file)
        for tl in test['teardown']:
            print(pp_line(tl), file=tests_file)
        for section_name, section_lines in test.get('teardown_detail', {}).items():
            print(f' # {section_name}:', file=tests_file)
            for sct_line in section_lines:
                print(' ', sct_line['msg'], file=tests_file)

