
import re
import time

def collect_tests(lines, verbosity=0):
    """ Collect and reorganise pytest results produced by k8s_test

    The returned dictionary has the following fields as applicable:
    - 'file': File the test was defined in
    - 'name': Name of the test
    - ('param': Extra parameters for the test)
    - ('status': Result of the test)
    - 'msgs': Log messages emitted while test was running (excluding teardown)
    - ('teardown': Log messages emitted while test was torn down)
    - ('teardown_status': Result status of teardown)
    - 'detail': Detailed information added by pytest later in the log
    - ('detail/main': Main exception log)
    - 'teardown_detail': Detailed information about teardown added by pytest later
    - ('teardown_detail/main': Teardown exception log)

    :param lines: Log lines
    :param verbosity: Whether to show a status message
    :returns: dictionary per test
    """

    start_time = time.time()
    tests = []
    test_start_re = re.compile('(?P<file>tests/[\w\d/_\-\.]+\.py)\:\:(?P<name>[\w\d/_\-\.]+)(?P<param>\[[^\]]*\])?')
    test_end_re = re.compile('(?P<status>[A-Z]+) (?P<msg>\([^\)]*\))? *\[[ ]*\d+\%\]$')
    test_teardown_re = re.compile('\-+\ [\w ]+ \-+')
    test_error_report_re = re.compile('=+ [A-Z]+ =+')

    def is_test_runner(line):
        # Filter out lines from non-makefile-runner pods
        return 'pod' in line and 'makefile-runner' in line['pod']

    # Go forward to session start (ignore initialisation)
    session_start_re = re.compile('(=+ test session starts =+|collected.*selected.*)')
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
        failed_teardown_prefix = test['file']+'::'+test['name']+' '
        if i < len(lines) and is_test_runner(lines[i]) and \
           test_teardown_re.match(lines[i]['msg']):

            teardown_lines = []
            while i < len(lines) and (not is_test_runner(lines[i]) or lines[i]['msg']):
                teardown_lines.append(lines[i])
                i += 1

            # Except if the teardown failed, which will be indicated
            # by an empty line followed by a 'FAILED' for the
            # test. Those two lines we also want.
            if i+1 < len(lines) and lines[i+1]['msg'].startswith(failed_teardown_prefix):
                teardown_lines.append(lines[i])
                teardown_lines.append(lines[i+1])
                m = test_end_re.search(lines[i+1]['msg'])
                if m:
                    test['teardown_status'] = m['status']
                i+=2

            test['teardown'] = teardown_lines

        # Alternatively we can also have a "naked" teardown failure, without log
        elif i < len(lines) and lines[i]['msg'].startswith(failed_teardown_prefix):
            m = test_end_re.search(lines[i]['msg'])
            if m:
                test['teardown_status'] = m['status']
            test['teardown'] = [lines[i]]
            i += 1
        

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
            i += 1

        # Complete reports
        sections[current_section] = current_lines
        test['detail' if occasion is None else occasion+'_detail'] = sections

    skipped += len(lines) - i
    if verbosity > 0:
        print(f'Finished, {len(lines)-skipped-start_line}/{len(lines)-start_line} lines of test report used '
              f'({time.time()-start_time:.2f} s)')
    return tests
