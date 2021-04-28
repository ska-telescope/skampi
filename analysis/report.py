
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

    def add_log(self, fname, log, source=None):

        # Extract test data, classify
        self.total_lines += len(log)
        test_data = tests.collect_tests(log, 1)
        matches = classifiers.classify_test_results(test_data)

        # Note all matches, but remove detailed test logs to save space
        self.matches_per_file[fname] = [ _strip_match(match) for match in matches ]

        # Extract date from first log message
        log_date = None
        for l in log:
            if 'time' in l:
                log_date = l['time']
                break
        if log_date is not None:

            for cfr in classifiers.classifiers:
                cfr_matches = [ match for match in matches if match['cfr'] is cfr ]
                if not cfr_matches:
                    continue
                cfr_matches_stripped = [ _strip_match(cfr_match) for cfr_match in cfr_matches ]

                # Add to list, retaining only a number of matches (as
                # we keep basically the entire log for them in
                # memory!)
                match_list = self.matches_per_clfr.get(cfr.skb, [])
                match_log = dict( date = log_date, log = log, log_id=self.log_id, cfr=cfr,
                                  name = fname, source = source, matches = cfr_matches )
                match_list.append(match_log)
                match_list = sorted(match_list, key=lambda match: match['date'], reverse=True)
                self.matches_per_clfr[cfr.skb] = match_list[:self.matches_per_clfr_count]

                # Retain stripped matches for all
                all_matches_list = self.all_matches_per_clfr.get(cfr.skb, [])
                match_log_stripped = dict(match_log)
                match_log_stripped['matches'] = cfr_matches_stripped
                all_matches_list.append(match_log_stripped)
                self.all_matches_per_clfr[cfr.skb] = list(all_matches_list)

        self.log_id += 1

    def add_tarball(self,tar):
        while True:
            # Read through tar file sequentially to minimise seeking
            info = tar.next()
            if info is None:
                return
            # Extract
            with tar.extractfile(info) as f:
                try:
                    self.add_log(info.name, logs.collect_file(info.name, 1, f))
                except Exception:
                    traceback.print_exc()

    def add_file_or_uri(self, fname):

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
                    self.add_tarball(tar)

            else:
                # Otherwise expect it to be a flat file
                self.add_log(_fname, logs.collect_file(fname, 1, bio))
            return

        # Assume it's a file. Tarball?
        if _is_tarball(fname):
            with tarfile.open(fname, mode='r:*') as tar:
                self.add_tarball(tar)
        else:
            self.add_log(fname, logs.collect_file(fname, 1))

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
                    self.add_file_or_uri(f'{uri}/{project}/-/jobs/{job.id}/artifacts/raw/{artifact}?inline=false')
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

        print(rstgen.header(1, cfr.skb + " " + cfr.message), file=f)

        total_matches = len(self.all_matches_per_clfr[cfr.skb])
        files_with_matches = { fname for fname, matches in self.matches_per_file.items()
                               if any( match['cfr'] is cfr for match in matches ) }
        files_matched_rel = len(files_with_matches) / max(1, len(self.matches_per_file))

        print(f'Found a total of {len(self.all_matches_per_clfr[cfr.skb])} matches in '
              f'{len(files_with_matches)} ({files_matched_rel*100:.1f}%) runs '
              f'{", ".join(sorted(files_with_matches))}\n',file=f)

        # Show example matches
        for cfr_match in self.matches_per_clfr[cfr.skb]:

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
                print(rstgen.header(2, f" {date} {test_name}"), file=f)

                print(f"See also :download:`{cfr_match['name']} <log-{cfr_match['log_id']}.txt>`"
                      f"{'' if cfr_match['source'] is None else ' (source ' + cfr_match['source'] + ')'}"
                      f", recorded {cfr_match['date']}\n", file=f)
                
                self.make_test_report(f, test, matches)

        return files_matched_rel
                
    def write_log(self, f, cfr_matches):

        # Indicate where log came from
        source = cfr_matches[0]['source']
        if source:
            print(f"Log {cfr_matches[0]['name']} retrieved from {source}, matched:", file=f)
        else:
            print(f"Log {cfr_matches[0]['name']}, matched:", file=f)

        # List matched classifiers, collecting lines to highlight
        to_highlight = {}
        for cfr_match in cfr_matches:
            print(f" * {cfr_match['cfr'].skb} {cfr_match['cfr'].message}", file=f)
            for match in cfr_match['matches']:
                for line in match['matched']:
                    if line['time'] not in to_highlight:
                        to_highlight[line['time']] = [cfr_match]
                    else:
                        to_highlight[line['time']].append(cfr_match)

        # Now pretty-print lines
        for l in cfr_matches[0]['log']:
            print(logs.pp_line(l), file=f)
            for cfr_match in to_highlight.get(l['time'], []):
                print(f" ^^ {cfr_match['cfr'].skb} {cfr_match['cfr'].message}", file=f)

    def write_logs(self, directory):

        # Collect all logs to generate
        logs_to_generate = {}
        for cfr in classifiers.classifiers:
            for cfr_match in self.matches_per_clfr[cfr.skb]:
                log_id = cfr_match['log_id']
                if log_id not in logs_to_generate:
                    logs_to_generate[log_id] = []
                logs_to_generate[log_id] += [
                    cfr_match for cfr_match in self.all_matches_per_clfr[cfr.skb]
                    if cfr_match['log_id'] == log_id
                ]

        # Generate them!
        for log_id, cfr_matches in logs_to_generate.items():
            with open(pathlib.Path(directory, f'log-{log_id}.txt'), 'w', encoding='utf-8') as f:
                self.write_log(f, cfr_matches)

