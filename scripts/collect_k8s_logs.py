# /bin/env python3
"""
Kubernetes log collection script

Usage:
  collect_k8s_logs.py <ns>... [--timefmt=<format>]
      [--pp=<out>] [--dump=<out>] [--tests=<out>] [--test=<out>]
      [--eval=<out>] [--eval-json=<out>] [-v <0,1>] [--pp-thread]

Options:
  <ns>             Namespaces or JSON dump files (files must have '/' or '.')
  --timefmt=<fmt>  Format timestamps (default %H:%M:%S.%f)
  --pp=<out>       Pretty-print to file ('-' for stdout - default)
  --dump=<out>     Write JSON strings to file ('-' for stdout)
  --tests=<out>    Put test case summary into file ('-' for stdout)
  --eval=<out>     Evaluate output against classifiers ('-' for stdout)
  --eval-json=<out> Evaluate, but given JSON output ('-' for stdout)
  --test=<test>    Filter out only test of given name
  --pp-thread      Include thread field in pretty-printed output
  -v <0,1>         Verbosity level for report (0: default, 1: show matched lines)
"""

import datetime
import json
import os
import re
import sys
import time
from datetime import timedelta, timezone

from docopt import docopt
from kubernetes import client, config

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis import classifiers, logs, tests

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()
v1 = client.CoreV1Api()

# Collect lines
arguments = docopt(__doc__, version="SKAMPI log analysis")
verbosity = arguments["-v"]
if verbosity is None:
    verbosity = 0
else:
    verbosity = int(verbosity)

lines = []
for namespace in arguments["<ns>"]:
    if "." in namespace or "/" in namespace:
        lines += logs.collect_file(namespace, verbosity)
    else:
        lines += logs.collect_pod_logs(v1, namespace)
        lines += logs.collect_events(v1, namespace)

lines = sorted(lines, key=lambda line: line["time"])

# Default is pretty-print to stdout
pp_target = arguments["--pp"]
dump_target = arguments["--dump"]
tests_target = arguments["--tests"]
eval_target = arguments["--eval"]
eval_json_target = arguments["--eval-json"]
if all(
    target is None
    for target in [pp_target, dump_target, tests_target, eval_target, eval_json_target]
):
    pp_target = "-"

# Small helper for printing to stdout/file
def make_target(target_name, message=""):
    if target_name is not None:
        if target_name == "-":
            yield sys.stdout
        else:
            print(message)
            # Small hack for GitLab CI - show expected URI
            if (
                os.getenv("CI_PROJECT_URL") is not None
                and os.getenv("CI_JOB_ID") is not None
            ):
                print(
                    f"  {os.getenv('CI_PROJECT_URL')}/-/jobs/{os.getenv('CI_JOB_ID')}/artifacts/file/{target_name}"
                )
            with open(target_name, "w", encoding="utf-8") as f:
                yield f


# Pretty-print
pp_date_format = arguments["--timefmt"]
if pp_date_format is None:
    pp_date_format = "%H:%M:%S.%f"
# https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")


def escape_ansi(line):
    return ansi_escape.sub("", line)


if arguments["--pp-thread"]:

    def pp_line(line):
        return f"{line['time'].strftime(pp_date_format)} {line.get('level', '---')}\t{line.get('pod', '---')}:{line.get('container', '---')}\t{line.get('thread', '---')}\t{escape_ansi(line['msg'])}"


else:

    def pp_line(line):
        if not line['time']:
            line['time'] = datetime.datetime(year=1970, month=1, day=1, tzinfo=datetime.timezone.utc)
        return f"{line['time'].strftime(pp_date_format)} {line.get('level', '---')}\t{line.get('pod', '---')}:{line.get('container', '---')}\t{escape_ansi(line['msg'])}"


for pp_file in make_target(pp_target, f"Pretty-printing to {pp_target}..."):
    for line in lines:
        print(pp_line(line), file=pp_file)

# Dump
for dump_file in make_target(dump_target, f"Dumping JSON to {dump_target}..."):
    for line in lines:
        print(
            json.dumps({**line, "time": logs.render_date(line["time"])}), file=dump_file
        )

# Find test cases
for tests_file in make_target(
    tests_target, f"Writing test report to {tests_target}..."
):

    # Done, print results
    for test in tests.collect_tests(lines, verbosity):
        if arguments["--test"] is not None:
            if test["name"] != arguments["--test"]:
                continue
        print(
            "\n===",
            test["status"],
            test["file"],
            test["name"],
            test.get("param", ""),
            "===",
            file=tests_file,
        )

        # Show test case report + detail
        for tl in test["msgs"]:
            print(pp_line(tl), file=tests_file)
        for section_name, section_lines in test.get("detail", {}).items():
            print(f" # {section_name}:", file=tests_file)
            for sct_line in section_lines:
                print(" ", sct_line["msg"], file=tests_file)

        # Teardown report?
        if "teardown" not in test:
            continue
        print("--- teardown ---", file=tests_file)
        for tl in test["teardown"]:
            print(pp_line(tl), file=tests_file)
        for section_name, section_lines in test.get("teardown_detail", {}).items():
            print(f" # {section_name}:", file=tests_file)
            for sct_line in section_lines:
                print(" ", sct_line["msg"], file=tests_file)

# Find test cases
for eval_file in make_target(eval_target, f"Writing evaluation to {eval_target}..."):

    # Evaluate classifiers
    triggers = classifiers.classify_test_results(tests.collect_tests(lines, verbosity))

    for trigger in triggers:

        # Show the trigger message
        cfr = trigger["cfr"]
        matched = trigger["matched"]
        test = trigger["test"]
        print(
            f"{'!! ' if cfr.taints else ''}{cfr.skb} {cfr.message}  "
            f"[{len(matched)} instance{'s' if len(matched)>1 else ''} "
            f"in {test['file']} {test['name']} {test['status']}"
            f"{', possibly more' if cfr.only_once else ''}]",
            file=eval_file,
        )

        # For high verbosity, also print the matched lines
        if verbosity >= 2:
            for match in matched:
                print("  ", pp_line(match), file=eval_file)

for eval_json_file in make_target(
    eval_json_target, f"Writing JSON evaluation to {eval_json_target}..."
):

    # Evaluate classifiers, write out result
    triggers = classifiers.classify_test_results(tests.collect_tests(lines, verbosity))
    outputs = []
    for trigger in triggers:
        outputs.append(
            {
                "source": arguments["<ns>"],
                "test": {
                    k: v
                    for k, v in trigger["test"].items()
                    if k not in ["msgs", "detail", "teardown", "teardown_detail"]
                },
                "cfr": {
                    "skb": trigger["cfr"].skb,
                    "message": trigger["cfr"].message,
                    "taints": trigger["cfr"].taints,
                    "harmless": trigger["cfr"].harmless,
                    "only_once": trigger["cfr"].only_once,
                    "suppresses": trigger["cfr"].suppresses,
                },
                "matched": [
                    {**l, "time": logs.render_date(l["time"])}
                    for l in trigger["matched"]
                ],
            }
        )
    json.dump(outputs, eval_json_file)
