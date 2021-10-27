"""
Functions for reading logs and events out of Kubernetes, as well
as (de)serialisation as JSON files.
"""

import datetime
import json
import re
import time
from datetime import timedelta, timezone

try:
    import orjson
except:
    orjson = json

import kubernetes

# Regular expressions
kube_time_re = re.compile(
    "^(?P<kube_time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{0,6})\d*Z (?P<rest>.*)"
)
ska_re = re.compile(
    "^1\|(?P<ska_time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d*Z)\|(?P<ska_level>[^\|]*)\|(?P<ska_thread>[^\|]*)\|(?P<ska_function>[^\|]*)\|(?P<ska_source>[^\|]*)\|(?P<ska_tags>[^\|]*)\|(?P<msg>.*)$"
)

# Standard datetime parsing tools
def parse_date(date):
    dt = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%f")
    return dt.replace(tzinfo=timezone.utc)


def render_date(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")


SAME_ATTRS_THRESHOLD = datetime.timedelta(milliseconds=0.1)


def parse_log_line(line: str, attrs: dict, previous: dict) -> dict:

    out = dict(attrs)

    # Parse Kubernetes timestamp
    m = kube_time_re.match(line)
    if not m:
        # This can happen with lines that are split with \r:
        # Kubernetes does not interpret this as a new-line (and
        # therefore adds only a single timestampe), yet Python's
        # splitlines does. Therefore we can just take over the
        # attributes from the last line.
        if previous:
            out.update(previous)
        else:
            print("could not parse K8s timestamp: ", line)
            out["time"] = None
    else:
        out["time"] = parse_date(m["kube_time"])
        line = m["rest"]

    # Attempt to parse SKA format
    m = ska_re.match(line)
    if m:
        out["ska_time"] = m["ska_time"]
        out["level"] = m["ska_level"]
        out["thread"] = m["ska_thread"]
        out["function"] = m["ska_function"]
        out["source"] = m["ska_source"]
        out["tags"] = {
            name_val[0]: name_val[1] if len(name_val) > 1 else None
            for name_val in [tag.split(":") for tag in m["ska_tags"].split(",")]
        }
        line = m["msg"]

    # If a line without SKA-specific annotations follows one with
    # them, assume that we are simply dealing with a log message that
    # included '\n', which have now been split over multiple lines
    elif (
        "ska_time" in previous
        and out.get("time") - previous.get("time") < SAME_ATTRS_THRESHOLD
    ):
        out["ska_time"] = previous["ska_time"]
        out["level"] = previous["level"]
        out["thread"] = previous["thread"]
        out["function"] = previous["function"]
        out["source"] = previous["source"]
        out["tags"] = previous["tags"]

    out["msg"] = line
    return out


def aggregate_status(dct, statuses):
    """Small helper for counting appearing levels"""

    if "level" in dct:
        if dct["level"] not in statuses:
            statuses[dct["level"]] = 1
        else:
            statuses[dct["level"]] += 1


def collect_pod_logs(api, namespace):
    ret = api.list_namespaced_pod(namespace, watch=False)
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
                    logs = api.read_namespaced_pod_log(
                        podName,
                        namespace,
                        previous=previous,
                        container=containerName,
                        timestamps=True,
                    )
                except kubernetes.client.rest.ApiException as e:

                    # Try to parse as JSON to figure out whether
                    # something strange happened. As we are
                    # speculatively asking for previous containers,
                    # 'not found' errors are quite expected
                    body = json.loads(e.body)
                    if not body["message"].endswith("not found"):
                        print(
                            f"While querying logs for pod {podName} container {containerName}: {e}"
                        )
                    continue
                attrs = {
                    "pod": podName,
                    "container": containerName,
                    "previous": previous,
                    "namespace": namespace,
                }
                line_dict = {}
                for line in logs.splitlines():
                    if len(line) > 0:

                        # Add line to list
                        line_dict = parse_log_line(line, attrs, line_dict)
                        lines.append(line_dict)
                        aggregate_status(line_dict, statuses)

        if "ERROR" in statuses or "CRITICAL" in statuses:
            print(
                f"  {podName}:",
                ", ".join([f"{n}x{level}" for level, n in statuses.items()]),
            )

    print(f"  ... {len(lines)} lines read")
    return lines


def collect_events(api, namespace):

    print(f"Obtaining events from namespace {namespace}...")
    lines = []
    api_response = api.list_namespaced_event(namespace, watch=False)
    cont_re = re.compile("^spec.containers{(?P<container>.*)}$")

    statuses = {}
    for item in api_response.items:
        if item.first_timestamp is not None:

            # Get attributes
            attrs = {"msg": item.message, "level": item.type}
            attrs[item.involved_object.kind.lower()] = item.involved_object.name
            attrs["namespace"] = item.involved_object.namespace
            if item.involved_object.field_path is not None:
                m = cont_re.match(item.involved_object.field_path)
                if m:
                    attrs["container"] = m["container"]

            # Generate line for first time stamp
            date_format = "%Y-%m-%d %H:%M:%S"
            lines.append({"time": item.first_timestamp, **attrs})
            aggregate_status(attrs, statuses)

            # Generate line for last time stamp
            if (item.last_timestamp - item.first_timestamp).total_seconds() != 0:
                lines.append({"time": item.last_timestamp, **attrs})
                aggregate_status(attrs, statuses)

    print(
        f"  ... {len(lines)} events:",
        ", ".join([f"{n}x{level}" for level, n in statuses.items()]),
    )

    return lines


def collect_file(filename, verbosity, fileobj=None):

    t = time.time()
    if verbosity > 0:
        print(f"Reading from {filename}...", flush=True)
    # Read JSON lines from a file
    lines = []
    with (open(filename, "r") if fileobj is None else fileobj) as f:
        for line in f:
            # Sometimes we end up with b'...'
            if isinstance(line, bytes):
                if line.startswith(b"b'{"):
                    line = line[2:-2].decode("unicode_escape")
                else:
                    line = line.decode("utf-8")
            if line.startswith("b'{"):
                line = line[2:-2].encode("utf-8").decode("unicode_escape")
            line_dict = orjson.loads(line)
            if "time" in line_dict:
                line_dict["time"] = parse_date(line_dict["time"])
            lines.append(line_dict)

    if verbosity > 0:
        print(f"  ... {len(lines)} lines read ({time.time() - t:.2f} s)", flush=True)
    return lines


# https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")


def pp_line(line, date_format="%H:%M:%S.%f", with_thread=False):

    # Get data
    time = line.get("time")
    if time is None:
        time = "???"
    else:
        time = time.strftime(date_format)
    level = line.get("level", "")
    pod = line.get("pod", "---")
    container = line.get("container", "---")
    message = ansi_escape.sub("", line["msg"])

    # Emit line
    if with_thread:
        thread = line.get("thread", "---")
        return f"{time} {level:>7} {pod}:{container}:{thread} | {message}"
    else:
        return f"{time} {level:>7} {pod}:{container} | {message}"


def collect_pod_timings(lines):
    """Finds first log message from each container for every pod.
    :param lines: Log lines
    :returns: Dictionary of (container, time) pairs
    """

    timings = {}
    pod_container = {}
    start = None
    for l in lines:

        # Get pod
        pod = l.get("pod")
        container = l.get("container")
        if pod is None or container is None:
            continue

        # Get container, check whether it's the current one
        if pod_container.get(pod) == container:
            continue
        pod_container[pod] = container

        # Add a new timing!
        if pod not in timings:
            timings[pod] = []
        timings[pod].append((container, l["time"]))

    return timings
