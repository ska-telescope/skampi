import urllib3
import rstgen
import io
import shutil
import tarfile
import traceback
import pathlib
import gitlab

from analysis import logs, tests, classifiers

cfrs_sorted = sorted(classifiers.classifiers, key=lambda cfr: cfr.skb)

def _strip_match(match):
    """ Strip detailed test log from a match to safe space """

    if not 'test' in match:
        return match

    test = dict(match['test'])
    if 'msgs' in test:
        del test['msgs']
    if 'teardown' in test:
        del test['teardown']
    if 'detail' in test:
        del test['detail']
    if 'teardown_detail' in test:
        del test['teardown_detail']

    match_stripped = dict(match)
    match_stripped['test'] = test
    return match_stripped

def _is_tarball(fname):
    return fname.endswith('.tar.gz') or fname.endswith('.tar.xz') or fname.endswith('.tar.bz2')

class Report:

    def __init__(self, matches_per_clfr_count = 3, context_lines = 30):

        # Parameters
        self.matches_per_clfr_count = matches_per_clfr_count
        self.context_lines = context_lines

        # Work structures
        self.http = urllib3.PoolManager()
        self.matches_per_file = {}
        self.matches_per_clfr = { cfr.skb: [] for cfr in cfrs_sorted }
        self.all_matches_per_clfr = { cfr.skb: [] for cfr in cfrs_sorted }
        self.total_lines = 0
        self.log_id = 0
        self.pod_timings = {}
        self.revisions = {}
        self.revision_files = {}
        self.file_date = {}

        # See build_maps()
        self.files_per_cfr = None

    def add_log(self, fname, log, source=None, revision=None):
        """ Adds a log to the report

        :param fname: (File) name of the log
        :param log: List of log lines as dictionaries
        :param source: Original source of the log, say if extracted from an URL
        :param sha: The Git revision associated witht the log
        """

        # Extract test data, classify
        self.total_lines += len(log)
        test_data = tests.collect_tests(log, 1)
        matches = classifiers.classify_test_results(test_data)

        # Note all matches, but remove detailed test logs to save space
        self.matches_per_file[fname] = [ _strip_match(match) for match in matches ]

        # Add to revision-file map
        if revision is not None:
            if revision not in self.revision_files:
                self.revision_files[revision] = set()
            self.revision_files[revision].add(fname)

        # Extract date from first log message
        log_date = None
        for l in log:
            if 'time' in l:
                log_date = l['time']
                break
        if log_date is not None:
            self.file_date[fname] = log_date

            # Add revision to dictionary, noting the latest date we have seen it
            # (for sorting later)
            if revision is not None and (revision not in self.revisions or
                                         self.revisions[revision] < log_date):
                self.revisions[revision] = log_date

            for cfr in classifiers.classifiers:
                cfr_matches = [ match for match in matches if match['cfr'] is cfr ]
                if not cfr_matches:
                    continue
                self.add_cfr_matches(fname, source, log, log_date, cfr, cfr_matches, revision)

            # Collect timings
            timings = logs.collect_pod_timings(log)
            for pod, pod_ts in timings.items():
                current_pod_ts = self.pod_timings.get(pod, {})
                # Note that theoretically a container can appear multiple times.
                # We ignore that here.
                for cont, cont_t in pod_ts:
                    if cont not in current_pod_ts:
                        current_pod_ts[cont] = []
                    current_pod_ts[cont].append((cont_t - log_date).total_seconds())
                self.pod_timings[pod] = current_pod_ts

        self.log_id += 1

    def add_cfr_matches(self, fname, source, log, log_date, cfr, cfr_matches, revision):

        # Strip test information
        cfr_matches_stripped = [ _strip_match(cfr_match) for cfr_match in cfr_matches ]

        # Add to list, retaining only a number of matches (as
        # we keep basically the entire log for them in
        # memory!)
        match_list = self.matches_per_clfr.get(cfr.skb, [])
        match_log = dict( date = log_date, log = log, log_id=self.log_id, cfr=cfr,
                          name = fname, source = source, matches = cfr_matches,
                          revision = revision )
        match_list.append(match_log)
        match_list = sorted(match_list, key=lambda match: match['date'], reverse=True)
        self.matches_per_clfr[cfr.skb] = match_list[:self.matches_per_clfr_count]

        # Retain stripped matches for all
        all_matches_list = self.all_matches_per_clfr.get(cfr.skb, [])
        match_log_stripped = dict(match_log)
        match_log_stripped['matches'] = cfr_matches_stripped
        del match_log_stripped['log']
        all_matches_list.append(match_log_stripped)
        self.all_matches_per_clfr[cfr.skb] = list(all_matches_list)

    def add_tarball(self, tar, source, revision=None):
        while True:
            # Read through tar file sequentially to minimise seeking
            info = tar.next()
            if info is None:
                return
            # Extract
            with tar.extractfile(info) as f:
                try:
                    self.add_log(info.name, logs.collect_file(info.name, 1, f), source, revision)
                except Exception:
                    traceback.print_exc()

    def add_file_or_uri(self, fname, revision=None):

        # Is a URI?
        if fname.startswith('http://') or fname.startswith('https://'):

            # Read it to a memory buffer
            bio = io.BytesIO()
            print(f"Retrieving {fname}...", flush=True)
            _fname = urllib3.util.parse_url(fname).path
            with self.http.request('GET', fname, preload_content=False) as r:
                # Get suggested file name from header
                if r.getheaders().get('Content-Disposition', '').startswith('attachment; filename="'):
                    _fname = r.getheaders().get('Content-Disposition')[22:-1]
                # Copy data
                shutil.copyfileobj(r, bio)
            print(f" ... got {len(bio.getvalue())} bytes.", flush=True)
            bio.seek(0)

            # Tarball?
            if _is_tarball(_fname):
                with tarfile.open(mode='r:*', fileobj=bio) as tar:
                    self.add_tarball(tar, fname, revision)
            else:
                # Otherwise expect it to be a flat file
                self.add_log(_fname, logs.collect_file(fname, 1, bio), fname, revision)
            return

        # Assume it's a file. Tarball?
        if _is_tarball(fname):
            with tarfile.open(fname, mode='r:*') as tar:
                self.add_tarball(tar, fname, revision)
        else:
            self.add_log(fname, logs.collect_file(fname, 1), revision)

    def add_from_gitlab(self, uri, header, project, search, job_names, artifact):

        # Get project, search for pipelines
        gl = gitlab.Gitlab(uri, **header)
        proj = gl.projects.get(project)
        pips = proj.pipelines.list(**search)
        print(f"Found {len(pips)} GitLab pipelines", flush=True)

        # Go through pipelines, look for matching jobs
        for pip in pips:

            # Find a (successful) job matching the desired name
            jobs = pip.jobs.list(scope='success', include_retried='yes')
            for job in ( job for job in jobs if job.name in job_names ):

                # (Attempt to) download the artefact
                try:
                    self.add_file_or_uri(f'{uri}/{project}/-/jobs/{job.id}/artifacts/raw/{artifact}?inline=false',
                                         pip.sha)
                except Exception:
                    traceback.print_exc()

    def make_matches_table(self, f):

        # Compose header from classifier names
        header = [ 'name' ]
        for cfr in cfrs_sorted:
            header.append(cfr.skb)

        # Now go through files
        rows = []
        match_count = { cfr.skb: 0 for cfr in classifiers.classifiers }
        for fname in sorted(self.matches_per_file.keys()):
            matches = self.matches_per_file[fname]
            row = [fname]
            for cfr in cfrs_sorted:
                cfr_matches = [ match for match in matches if match['cfr'] is cfr ]
                if cfr_matches:
                    row.append('X')
                    match_count[cfr.skb] += 1
                else:
                    row.append('')
            rows.append(row)

        # Add a table with the count at the end
        rows.append(["Sum:"] + [ str(match_count[cfr.skb]) for cfr in cfrs_sorted])
        print(rstgen.table(header, rows), file=f)

    def build_maps(self):

        # Files that match a given classifier
        self.files_per_cfr = {
            cfr.skb: { fname for fname, matches in self.matches_per_file.items()
                       if any( match['cfr'] is cfr for match in matches ) }
            for cfr in classifiers.classifiers
        }

    def make_overview_table(self, f, revision=None):

        # Print a header
        if revision is None:
            files = self.matches_per_file.keys()
        else:
            files = self.revision_files[revision]
        file_count = len(files)
        print(f"Covering {file_count} logs.", file=f)
        if file_count > 0:
            files_sorted = sorted(files, key = lambda fname: self.file_date.get(fname))
            print(f"Date range: {self.file_date[files_sorted[0]]} to {self.file_date[files_sorted[-1]]}\n", file=f)

        # Start composing table
        header = [ '**SKB**', '**Message**', '**Affected Runs**', '**Last**', '**Cross-Check**'  ]
        rows = []
        for cfr in sorted(cfrs_sorted, key=lambda cfr: len(self.files_per_cfr[cfr.skb]),
                          reverse=True):

            matches = self.all_matches_per_clfr[cfr.skb]
            files_with_matches = self.files_per_cfr[cfr.skb]

            # Specialise to revision, if requested.
            if revision is not None:

                # Skip rows that have no matches globally (so we don't
                # repeat them for every revision).
                if not matches:
                    continue

                matches = [ cfr_match for cfr_match in matches if cfr_match['revision'] == revision]
                files_with_matches = files_with_matches & self.revision_files[revision]
            files_matched_rel = len(files_with_matches) / file_count

            # Include date + link to latest match
            if matches:
                last_match = sorted(matches, key=lambda match: match['date'])[-1]
                # Generate link - if it is one of the matches we are keeping
                if any( cfr_match['log_id'] == last_match['log_id']
                        for cfr_match in self.matches_per_clfr[cfr.skb] ):
                    last_ref = f":ref:`{last_match['date']} <{cfr.skb}-{last_match['log_id']}>`"
                else:
                    last_ref = last_match['date']
            else:
                last_ref = ""

            # Determine whether another kind of error appears to happen more often
            other_skb_changes = ''
            if files_with_matches:

                # Collect number of runs that fail for other classifiers as well
                cfr_intersection = {
                    cfr2.skb: len(self.files_per_cfr[cfr2.skb] & files_with_matches)
                    for cfr2 in classifiers.classifiers
                }

                # Determine ratio of those other failures in relation
                # to our failures with the ratio to all runs.  Filter
                # out classifiers that did not happen, this SKB - as
                # well as taints if this classifier likely caused the
                # taint.
                cfr_intersection_changes = sorted([
                    (cfr2, cfr_intersection[cfr2.skb] / len(files_with_matches) -
                           len(self.files_per_cfr[cfr2.skb]) / file_count)
                    for cfr2 in classifiers.classifiers
                    if len(self.files_per_cfr[cfr2.skb]) > 0 and cfr2.skb != cfr.skb and
                       (not cfr.taints or not cfr2.skb.startswith('TAINT'))
                ], key=lambda skb_diff: skb_diff[1], reverse=True)

                other_skb_changes = ", ".join( f":ref:`{cfr2.skb} <{cfr2.skb}>`: {change*100:+.1f}%"
                                               for cfr2, change in cfr_intersection_changes[:3]
                                               if change > 0 )

            rows.append( [ f":ref:`{cfr.skb} <{cfr.skb}>`", cfr.message,
                           f"{len(files_with_matches)} ({files_matched_rel*100:.1f}%)",
                           last_ref, other_skb_changes ] )


        print(rstgen.table(header, rows), file=f)

    def make_log_block(self, f, log, highlight_lines):

        # Find log lines to highlight
        to_highlight = sorted([ i for i, l in enumerate(log)
                                if l.get('time') in highlight_lines ])
        if not to_highlight:
            to_highlight = [0, len(log)-1]
        #print(to_highlight)

        # Go through log lines, decide what to do
        skipping = False
        lines_out = []
        highlight_out = []
        for i, l in enumerate(log):

            while to_highlight and i > to_highlight[0] + self.context_lines:
                to_highlight.pop(0)

            # Done?
            if not to_highlight:
                if not skipping:
                    lines_out.append(f'  ... {len(log)-i} lines skipped ...')
                break

            # Skip?
            if i < to_highlight[0] - self.context_lines:
                if not skipping:
                    lines_out.append(f'  ... {to_highlight[0]-i-self.context_lines} lines skipped ...')
                    skipping = True
                continue

            # Show line
            lines_out.append('  ' + logs.pp_line(l))
            if l.get('time') in highlight_lines:
                highlight_out.append(len(lines_out))
            skipping = False

        print(".. code-block:: none", file=f)
        if highlight_out:
            print(f"  :emphasize-lines: {','.join(str(i) for i in highlight_out)}", file=f)
        print(file=f)
        for s in lines_out:
            print(s, file=f)
        print(file=f)

    def make_test_report(self, f, test, matches):

        # Get the timestamps of all lines that matched. We assume those to
        # be unique.
        match_lines = set()
        for match in matches:
            match_lines |= { line['time'] for line in match['matched'] }

        # Print test data
        self.make_log_block(f, test['msgs'], match_lines)
        for section_name, section_lines in test.get('detail', {}).items():
            print(f'{section_name}:\n', file=f)
            self.make_log_block(f, section_lines, match_lines)

        if 'teardown' not in test:
            return
        print(rstgen.header(4, f"Teardown"), file=f)
        self.make_log_block(f, test['teardown'], match_lines)
        for section_name, section_lines in test.get('teardown_detail', {}).items():
            print(f'{section_name}:\n', file=f)
            self.make_log_block(f, section_lines, match_lines)

    def make_cfr_report(self, f, cfr):

        print(f".. _{cfr.skb}:\n", file=f)
        print(rstgen.header(1, cfr.skb + " " + cfr.message), file=f)

        total_matches = len(self.all_matches_per_clfr[cfr.skb])
        files_with_matches = self.files_per_cfr[cfr.skb]
        files_matched_rel = len(files_with_matches) / max(1, len(self.matches_per_file))

        print(f'Found a total of {len(self.all_matches_per_clfr[cfr.skb])} matches in '
              f'{len(files_with_matches)} ({files_matched_rel*100:.1f}%) runs '
              f'{", ".join(sorted(files_with_matches))}\n',file=f)

        # Show example matches
        for cfr_match in self.matches_per_clfr[cfr.skb]:

            first = True
            def test_id(match):
                return (match['test']['file'], match['test']['name'], match['test'].get('param'))
            for tid in { test_id(match) for match in cfr_match['matches'] }:

                # Get all data
                matches = [ match for match in cfr_match['matches']
                            if test_id(match) == tid ]
                test = matches[0]['test']

                # Show header for test
                if 'param' in test:
                    test_name = f"{test.get('status')} test {test['file']}::{test['name']}[{test['param']}]"
                else:
                    test_name = f"{test.get('status')} test {test['file']}::{test['name']}"

                date = cfr_match['date'].strftime('%Y-%m-%d')
                if first:
                    print(f".. _{cfr.skb}-{cfr_match['log_id']}:\n", file=f)
                    first = False
                print(rstgen.header(2, f" {date} {test_name}"), file=f)

                print(f"See also :download:`{cfr_match['name']} <log-{cfr_match['log_id']}.txt>`"
                      f"{'' if cfr_match['source'] is None else ' (source ' + cfr_match['source'] + ')'}"
                      f", recorded {cfr_match['date']}\n", file=f)

                self.make_test_report(f, test, matches)

        return files_matched_rel

    def write_log(self, f, cfr_match):

        # Indicate where log came from
        source = cfr_match['source']
        if source:
            print(f"Log {cfr_match['name']} retrieved from {source}, matched:", file=f)
        else:
            print(f"Log {cfr_match['name']}, matched:", file=f)

        # List matched classifiers, collecting lines to highlight
        to_highlight = {}
        other_matches = self.matches_per_file[cfr_match['name']]
        for other in other_matches:
            print(f" * {other['cfr'].skb} {other['cfr'].message}", file=f)
            for line in other['matched']:
                if line['time'] not in to_highlight:
                    to_highlight[line['time']] = [other]
                else:
                    to_highlight[line['time']].append(other)

        # Now pretty-print lines
        for l in cfr_match['log']:
            print(logs.pp_line(l), file=f)
            for other in to_highlight.get(l['time'], []):
                print(f" ^^ {other['cfr'].skb} {other['cfr'].message}", file=f)

    def write_logs(self, directory):

        # Collect all logs to generate
        logs_to_generate = {}
        for cfr in classifiers.classifiers:
            for cfr_match in self.matches_per_clfr[cfr.skb]:
                logs_to_generate[cfr_match['log_id']] = cfr_match

        # Generate them!
        for log_id, cfr_match in logs_to_generate.items():
            with open(pathlib.Path(directory, f'log-{log_id}.txt'), 'w', encoding='utf-8') as f:
                self.write_log(f, cfr_match)

        return len(logs_to_generate)

    def make_pod_timing_table(self, f):

        # Determine average start
        pod_timings_avg = {
            pod : {
                cont : sum(ts) / len(ts)
                for cont, ts in pod_conts.items()
            } for pod, pod_conts in self.pod_timings.items()
            if all(len(ts) > 1 for ts in pod_conts.values())
        }

        if not pod_timings_avg:
            return
        max_stages = max( len(container) for container in pod_timings_avg.values() )
        header = ['**Pod**'] + [''] * max_stages

        # Go through pods sorted by last average finish
        pods_sorted = sorted( pod_timings_avg.items(),
                              key = lambda pod_map: max(pod_map[1].values()) )
        rows = []
        for pod, cont_avgs in pods_sorted:

            # Right-justify the row
            row = [pod] + (max_stages - len(cont_avgs)) * ['']
            for cont, avg in sorted(cont_avgs.items(), key=lambda cont_avg: cont_avg[1]):
                row.append(f"{cont}: {avg:.2f} s")
            rows.append(row)

        print(rstgen.table(header, rows), file=f)

        
