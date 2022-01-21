"""
Classification of test results as produced by collect_tests()

The general approach here is that each classifier runs on the results
of certain test, and matches lines in the different log sections. This
can be used for automatically scanning for events.
"""

import datetime
import os
import pathlib
import re
import time

__all__ = ["classifiers", "classify_by_test"]


class Classifier:
    """Test classifier

    :param tests: Tests to match, as (file, name as reported by pytest). (None, None) matches all tests
    :param predicates: Checks for a test, given as a function
    :param skb: SKB code to identify classifier
    :param msg: Message to show explaining what happend
    :param taints: Should we disregard further test results if this happens?
    :param harmless: Assume this would not be responsible for a test failure
    :param only_once: Log only once
    :param suppresses: Codes of other classifiers to suppress after this one was matched
    """

    def __init__(
        self,
        tests,
        predicates,
        skb,
        message,
        taints=False,
        harmless=False,
        only_once=False,
        suppresses=[],
    ):
        self.tests = tests
        self.predicates = predicates
        self.skb = skb
        self.message = message
        self.taints = taints
        self.harmless = harmless
        self.only_once = only_once
        self.suppresses = suppresses

    def __call__(self, *args, **kwargs):
        for predicate in self.predicates:
            i = predicate(*args, **kwargs)
            if i:
                return i
        return False


ATTR_EQUIVALENTS = {
    "subarraynode1-sa1-0": {"subarraynode-sa1-0", "subarraynode-01-0"},
    "subarraynode2-sa2-0": {"subarraynode-sa2-0", "subarraynode-02-0"},
    "subarraynode3-sa3-0": {"subarraynode-sa3-0", "subarraynode-03-0"},
    "cspsubarrayleafnode1-01-0": {"cspsubarrayleafnode-01-0"},
    "cspsubarrayleafnode2-02-0": {"cspsubarrayleafnode-02-0"},
    "cspsubarrayleafnode3-03-0": {"cspsubarrayleafnode-03-0"},
    "sdpsubarrayleafnode1-01-0": {"sdpsubarrayleafnode-01-0"},
    "sdpsubarrayleafnode2-02-0": {"sdpsubarrayleafnode-02-0"},
    "sdpsubarrayleafnode3-03-0": {"sdpsubarrayleafnode-03-0"},
    "dishleafnode1-01-0": {"dishleafnode-01-0"},
    "dishleafnode2-02-0": {"dishleafnode-02-0"},
    "dishleafnode3-03-0": {"dishleafnode-03-0"},
}

QUICKSCAN_TAGS = ["container", "pod", "level", "source", "thread", "msg"]

# Message match predictate
def match_msg(
    msg_r,
    after_msg_r=None,
    after_msg_attrs={},
    section="msgs",
    missing=False,
    max_time=None,
    max_count=None,
    **kwargs,
):
    """Regex-match a message of given warning level
    :param msg_r: Regular expression for message to match
    :param after_msg_r: Must appear after matching a message (in same log)
    :param after_msg_attrs: Message above must also have given attributes
    :param section: Section to search for message
    :param missing: Inverse predicate - trigger if message does *not* appear
    :param max_time: Must appear within given number of seconds from first message
    :param max_count: Must appear within given number of lines
    :param matched: Output parameter for lines matched
    """

    # Compile regular expressions
    msg_rc = re.compile(msg_r)
    after_msg_rc = None if after_msg_r is None else re.compile(after_msg_r)

    # Convert attributes to sets (if not already), applying equivalences
    msg_attrs = dict(kwargs)
    for attrs in [msg_attrs, after_msg_attrs]:
        for k, vals in attrs.items():
            vals_new = set()
            for v in vals if isinstance(vals, set) else [vals]:
                vals_new.add(v)
                if v in ATTR_EQUIVALENTS:
                    vals_new |= ATTR_EQUIVALENTS[v]
            attrs[k] = vals_new

    # Optimised version if we scanning for something in "msgs" with given attributes
    if (
        section == "msgs"
        and after_msg_r is None
        and max_time is None
        and max_count is None
    ):

        # Make a composed regular expression for quickly scanning the entire text
        t = "\n\n#(?P<line>\d*)\n"

        def attr_match(k):
            if k == "msg":
                return msg_r
            if k not in msg_attrs:
                return ".*"
            if len(msg_attrs[k]) == 1:
                return re.escape(next(iter(msg_attrs[k])))
            return "(" + "|".join(re.escape(v) for v in msg_attrs[k]) + ")"

        t += "\n".join(attr_match(k) for k in QUICKSCAN_TAGS)
        t_rc = re.compile(t)

        # Scan
        def check(test, matched):
            i = 0
            for match in t_rc.finditer(test["msgs_t"]):
                l = test["msgs"][int(match["line"])]
                # Recheck, just to make sure (we might be checking extra attributes)
                if all(
                    l.get(k, "") in v_set for k, v_set in msg_attrs.items()
                ) and msg_rc.match(l["msg"]):
                    i += 1
                    if matched is not None:
                        matched.append(l)
            if missing:
                return 0 if i > 0 else 1
            else:
                return i

        return check

    def check(test, matched):
        # Traverse dictionary to get element containing lines
        elem = test
        for key in section.split("/"):
            if key not in elem:
                return missing
            elem = elem[key]
        i = 0
        # Go through lines in section
        end_time = None
        found_after = after_msg_r is None
        for l in elem:
            # Didn't find initial line yet?
            if not found_after:
                if any(
                    l.get(k, "") not in v_set for k, v_set in after_msg_attrs.items()
                ):
                    continue
                if not after_msg_rc.match(l["msg"]):
                    continue
                found_after = True
                if max_time is not None and l.get("time"):
                    end_time = l["time"] + datetime.timedelta(seconds=max_time)
                continue
            # Note time of first message
            if max_time is not None and end_time is None and l.get("time"):
                end_time = l["time"] + datetime.timedelta(seconds=max_time)
            # ... so we can stop at a point, if requested
            if max_time is not None and "time" in l and l["time"] > end_time:
                break
            # Check whether attributes and message match
            if all(
                l.get(k, "") in v_set for k, v_set in msg_attrs.items()
            ) and msg_rc.match(l["msg"]):
                i += 1
                if matched is not None:
                    matched.append(l)

        if missing:
            # Do not trigger if "after" message was not found
            if after_msg_r is not None and not found_after:
                return 0
            return not i
        return i

    return check


def match_status(*states):
    return lambda test, _: test["status"] in states


def match_and(*predicates):
    def check(*args, **kwargs):
        for p in predicates:
            if not p(*args, **kwargs):
                return False
        return True

    return check


# Check whether a certain test file exists, possibly replace
TEST_DIRECTORY = pathlib.Path(__file__).parent.parent.joinpath("post-deployment")

# Classifiers - simple map of pairs for now
classifiers = []
classifier_by_test = {}


def add_classifier(tests, *args, **kwargs):
    cfr = Classifier(tests, *args, **kwargs)
    classifiers.append(cfr)
    for test_id in tests:
        assert len(test_id) == 2
        if test_id not in classifier_by_test:
            classifier_by_test[test_id] = []
        classifier_by_test[test_id].append(cfr)

        # Check whether test file exists
        if test_id[1] is None:
            continue
        path_to_check = test_id[0]
        if not TEST_DIRECTORY.joinpath(path_to_check).exists():
            print(
                f"Test file {test_id[0]} not found locally! Check {cfr.skb} classifier!"
            )
            fname = pathlib.Path(test_id[0]).name
            for root, dirs, files in os.walk(TEST_DIRECTORY):
                if fname in files:
                    path2 = (
                        pathlib.Path(root).relative_to(TEST_DIRECTORY).joinpath(fname)
                    )
                    print(
                        f' ... speculatively replacing ("{test_id[0]}", "{test_id[1]}") by ("{path2}", "{test_id[1]}")'
                    )
                    path_to_check = str(path2)
                    test_id2 = (str(path2), test_id[1])
                    if test_id2 not in classifier_by_test:
                        classifier_by_test[test_id2] = []
                    classifier_by_test[test_id2].append(cfr)

        if TEST_DIRECTORY.joinpath(path_to_check).exists():
            # Check that test exists in given file
            rc_testdef = re.compile("def " + re.escape(test_id[1]) + "\(")
            with open(TEST_DIRECTORY.joinpath(path_to_check)) as f:
                found = False
                for l in f:
                    if rc_testdef.match(l):
                        found = True
                        break
            if not found:
                print(
                    f"Test {test_id[1]} not found in {path_to_check}! Check {cfr.skb} classifier!"
                )


# Add classifiers - most of them disabled for now

# add_classifier(
#     [
#         ("tests/smoke/test_mvp_clean.py", "test_is_running"),
#         (
#             "tests/acceptance/end_uses/maintain_telescope/switch_on_of_controller_elements/test_mvp_start_up.py",
#             "test_start_up",
#         ),
#     ],
#     [match_msg(r".*some of the dishes are ON.*")],
#     "SKBX-000",
#     "Some dishes start up in ON?",
# )
# add_classifier(
#     [
#         ("tests/smoke/test_devices.py", "test_dish_in_idle"),
#         ("tests/smoke/test_devices.py", "test_dish_not_on_at_start"),
#     ],
#     [match_status("XFAIL")],
#     "SKBX-002",
#     "Some dishes start up in ON?",
# )
# add_classifier(
#     [("tests/smoke/test_landing_page_loads.py", "test_landing_page_loads")],
#     [
#         match_msg(
#             r".*AssertionError: Expected <400> to be equal to <200>.*",
#             section="detail/main",
#         )
#     ],
#     "SKBX-003",
#     "Trying to access landing page yields error 400",
# )
# add_classifier(
#     [("tests/smoke/test_landing_page_loads.py", "test_landing_page_loads")],
#     [
#         match_and(
#             match_msg(
#                 r".*AssertionError: Expected <400> to be equal to <200>.*",
#                 section="detail/main",
#                 missing=True,
#             ),
#             match_status("FAILED"),
#         )
#     ],
#     "SKBX-003b",
#     "Trying to access landing page fails silently",
# )
# add_classifier(
#     [("tests/smoke/test_logging_namespace.py", "test_logging_namespace")],
#     [match_msg(r".*\[Errno 113\] No route to host.*")],
#     "SKBX-004",
#     "Elastic search deployment is assumed?",
# )
# add_classifier(
#     [("tests/smoke/test_logging_namespace.py", "test_logging_namespace")],
#     [match_msg(r".*\[Errno 113\] No route to host.*")],
#     "SKBX-005",
#     "Elastic search deployment is assumed?",
# )
# add_classifier(
#     [("tests/smoke/test_validate_device_spec.py", "test_ska_devices")],
#     [
#         match_msg(r"Property \[SkaLevel\] differs.*"),
#         match_msg(r"Command differs, \[GetVersionInfo\].*"),
#         match_msg(r"Attribute differs, \[(adminMode,)?(healthState,)?versionId\].*"),
#     ],
#     "SKBX-006",
#     "Not all SKA devices comply to spec at present",
# )
# add_classifier(
#     [("tests/smoke/test_validate_device_spec.py", "test_ska_devices")],
#     [match_and(match_msg(r"INFO.*", missing=True), match_status("XFAIL"))],
#     "SKBX-006b",
#     "test_ska_devices fails silently",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/configure_scan/test_XR-13_A2-Test.py",
#             "test_configure_subarray",
#         ),
#         (
#             "tests/acceptance/end_uses/conduct_observation/edit_subarray_resources/test_XR-13_A1.py",
#             "test_allocate_resources",
#         ),
#     ],
#     [
#         match_msg(
#             r".*",
#             after_msg_r=r"Parsing processing block.*",
#             max_time=10,
#             missing=True,
#             container="proccontrol",
#         ),
#     ],
#     "SKBX-007",
#     "Processing controller does not seem to react?",
#     taints=True,
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/configure_scan/test_XR-13_A2-Test.py",
#             "test_configure_subarray",
#         ),
#         (
#             "tests/acceptance/end_uses/conduct_observation/edit_subarray_resources/test_XR-13_A1.py",
#             "test_allocate_resources",
#         ),
#     ],
#     [
#         match_msg(
#             r".*",
#             after_msg_r=r"Deploying .* workflow .*, version .*",
#             max_time=10,
#             missing=True,
#             container="helmdeploy",
#         ),
#     ],
#     "SKBX-007b",
#     "Helm deployer does not seem to react?",
#     taints=True,
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/run_a_scan/test_XTP-1561.py",
#             "test_scan_id",
#         )
#     ],
#     [
#         match_msg(
#             r".*Expected all masters' dev state to be \('OFF', 'STANDBY'\) "
#             r"but instead found \['mid_csp_cbf/sub_elt/master'\] to be ON",
#             section="detail/main",
#         ),
#     ],
#     "SKBX-008",
#     "CSP master is not OFF",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/run_a_scan/test_XTP-826.py",
#             "test_multi_scan",
#         ),
#         (
#             "tests/acceptance/end_uses/monitor_observation/test_XTP-1772.py",
#             "test_recovery_from_aborted",
#         ),
#         (
#             "tests/acceptance/end_uses/conduct_observation/edit_subarray_resources/test_XTP-776_XTP-782.py",
#             "test_release_resources",
#         ),
#     ],
#     [
#         match_and(
#             match_msg(
#                 r".*Command On not allowed when the device is in OFF state.*",
#                 pod="cspmasterleafnode-01-0",
#                 level="ERROR",
#             ),
#             match_msg(
#                 r"E           mid_csp/elt/master timed out.*", section="detail/main"
#             ),
#         )
#     ],
#     "SKBX-009",
#     "CSP master leaf node fails to invoke On() in OFF state",
#     taints=True,
# )
# add_classifier(
#     [("tests/smoke/test_mvp_clean.py", "test_is_running")],
#     [
#         match_msg(r".*general exception whilst running telescope.*"),
#     ],
#     "SKBX-010",
#     "Could not query to check whether telescope was running?",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/edit_subarray_resources/test_XR-13_A1.py",
#             "test_allocate_resources",
#         ),
#         (
#             "tests/acceptance/end_uses/conduct_observation/configure_scan/test_XR-13_A2-Test.py",
#             "test_configure_subarray",
#         ),
#     ],
#     [
#         match_msg(
#             r"Message: 'Subarray healthState event returned unknown value.*",
#             pod="subarraynode1-sa1-0",
#         ),
#     ],
#     "SKBX-011",
#     "Subarray node complains about unknown healthState value?",
#     harmless=True,
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(r"\d+ \[\d+\] (INFO|DEBUG).*", pod="sdp-lmc-subarray-01-0"),
#     ],
#     "SKBX-012",
#     "SDP subarray duplicates (Tango?) log lines",
#     harmless=True,
#     only_once=True,
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(r"\d+ \[\d+\] (INFO|DEBUG).*", pod="sdp-lmc-master-0"),
#     ],
#     "SKBX-012b",
#     "SDP master duplicates (Tango?) log lines",
#     harmless=True,
#     only_once=True,
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/configure_scan/test_XR-13_A2-Test.py",
#             "test_configure_subarray",
#         )
#     ],
#     [
#         match_msg(
#             r"E.*tm_subarray_node.*receptorIDList.*current val=\(1, 2, 3, 4, 1, 2\).*",
#             section="detail/main",
#         )
#     ],
#     "SKBX-013",
#     "TM subarray node double-assigns receptors?",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/maintain_telescope/switch_on_of_controller_elements/test_mvp_start_up.py",
#             "test_start_up",
#         )
#     ],
#     [match_msg(r".*devices behind:\s*$", after_msg_r=r"transition: OFF.*")],
#     "SKBX-014",
#     "Devices transition to OFF behind central node",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/maintain_telescope/switch_on_of_controller_elements/test_mvp_start_up.py",
#             "test_start_up",
#         )
#     ],
#     [match_msg(r".*devices behind:\s*$", after_msg_r=r"transition: ON.*")],
#     "SKBX-014b",
#     "Devices transition to ON behind central node",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/edit_subarray_resources/test_XR-13_A1.py",
#             "test_allocate_resources",
#         ),
#         (
#             "tests/acceptance/end_uses/conduct_observation/edit_subarray_resources/test_XR-13_A4-Test.py",
#             "test_deallocate_resources",
#         ),
#         (
#             "tests/acceptance/end_uses/maintain_subarray/restart_aborted_subarray/test_XTP-1106.py",
#             "test_subarray_restart",
#         ),
#         (
#             "tests/acceptance/end_uses/conduct_observation/run_a_scan/test_XTP-826.py",
#             "test_multi_scan",
#         ),
#         (
#             "tests/acceptance/end_uses/monitor_observation/reset_an_aborted_observation/test_XTP-1096.py",
#             "test_subarray_obsreset",
#         ),
#     ],
#     [
#         match_msg(
#             r".*where False = telescope_is_in_standby\(\).*",
#             after_msg_r=".*assert[ \(]telescope_is_in_standby\(.*",
#             section="detail/main",
#         )
#     ],
#     "SKBX-015",
#     "Telescope not in standby at start of test",
#     taints=True,
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/run_a_scan/test_XTP-1561.py",
#             "test_scan_id",
#         )
#     ],
#     [match_msg(r".*INCONSISTENT state.*", section="detail/main")],
#     "SKBX-015b",
#     "Telescope master devices not in consistent state at start of test",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/test_XTP-813.py",
#             "test_mode_transitions",
#         )
#     ],
#     [
#         match_and(
#             match_msg(r"Dish transitioned to the 'STANDBY_FP'.*"),
#             match_msg(
#                 r".*timed out waiting for .*/master\.dishMode to change from STANDBY_FP.*",
#                 section="detail/main",
#             ),
#         )
#     ],
#     "SKB-31",
#     "test_mode_transitions sometimes times out waiting for dishMode change",
# )
# # add_classifier(
# #    [(None, None)],
# #    [match_msg(r"deleting pod for node scale down.*", level='Normal'),
# #     match_msg(r"deleting pod for node scale down.*", section='teardown', level='Normal'),
# #     match_msg(r"Stopping container.*", level='Normal'),
# #     match_msg(r"Stopping container.*", section='teardown', level='Normal')],
# #    "SKBX-016", "Kubernetes starts killing pods mid-test?", taints=True
# # )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/configure_scan/test_XR-13_A2-Test.py",
#             "test_configure_subarray",
#         )
#     ],
#     [
#         match_msg(
#             r".*mid_d0001/elt/master timed out whilst waiting for pointingState to change from TRACK to READY.*",
#             section="teardown_detail/main",
#         )
#     ],
#     "SKBX-017",
#     "Teardown fails to get dish to stop TRACKing",
#     taints=True,
# )
# add_classifier(
#     [(None, None)],
#     [match_msg(r".*DevError.*The polling thread is late", pod="subarraynode1-sa1-0")],
#     "SKBX-018",
#     "Tango polling thread goes out of synch on TM",
#     harmless=True,
#     only_once=True,
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(
#             r".*DevError.*The polling thread is late",
#             level="ERROR",
#             pod="dishleafnode1-01-0",
#         )
#     ],
#     "SKBX-018b",
#     "Tango polling thread goes out of synch on Dish",
#     harmless=True,
#     only_once=True,
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(
#             r"API_PollThreadOutOfSync",
#             level="WARNING",
#             pod="midcspsubarray01-subarray1-0",
#         )
#     ],
#     "SKBX-018c",
#     "Tango polling thread goes out of synch on CSP",
#     harmless=True,
#     only_once=True,
# )

# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/configure_scan/test_XR-13_A2-Test.py",
#             "test_configure_subarray",
#         )
#     ],
#     [
#         match_and(
#             match_msg(
#                 r"assigned receptors:\[1, 2\]",
#                 pod="midcspsubarray01-subarray1-0",
#                 section="teardown",
#             ),
#             match_msg(
#                 r".*timed out whilst waiting for receptorIDList to change from \(1, 2\) in.*",
#                 section="teardown_detail/main",
#             ),
#         )
#     ],
#     "SKBX-019",
#     "Test incorrectly expects receptor list to change while tearing down? Similar to SKB-31?",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/monitor_observation/reset_an_aborted_observation/test_XTP-1096.py",
#             "test_subarray_obsreset",
#         )
#     ],
#     [match_msg(r"KeyError: 'dish_client'", section="teardown")],
#     "SKBX-020",
#     "Dish leaf node fails with KeyError: 'dish_client' in teardown",
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(
#             r".*reason = Command StandByTelescope is not allowed in current state FAULT.",
#             section="teardown_detail/main",
#         )
#     ],
#     "SKBX-021",
#     "Trying to move a telescope in FAULT to standby",
#     taints=True,
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(
#             r".*Server encountered error 504 Gateway Timeout:", section="detail/main"
#         )
#     ],
#     "SKBX-022",
#     "OET encounteres a gateway timeout, ends up with 0 scripts",
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(
#             r"E.*Exception: .* is asserted to be ON but was instead OFF.*",
#             section="teardown_detail/main",
#         )
#     ],
#     "SKBX-023",
#     "Teardown fails due to devices already being OFF",
#     taints=True,
# )
# add_classifier(
#     [("tests/smoke/test_mvp_clean.py", "test_smell_mvp")],
#     [
#         match_msg(
#             r".*Device.*is not exported \(hint: try starting the device server\)",
#             section="detail/main",
#         )
#     ],
#     "SKBX-024",
#     "Sometimes startup is incomplete",
#     taints=True,
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/test_XTP-813.py",
#             "test_mode_transitions",
#         )
#     ],
#     [
#         match_and(
#             match_msg(r".*Dish state set to 'STANDBY'\..*", pod="dishmaster1-01-0"),
#             match_msg(
#                 r"E.*Expected <ON> to be equal to <STANDBY>, but was not\..*",
#                 section="detail/main",
#             ),
#         )
#     ],
#     "SKBX-025a",
#     "Dish master in state ON after claiming to transition to STANDBY",
#     taints=True,
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/test_XTP-813.py",
#             "test_mode_transitions",
#         )
#     ],
#     [
#         match_and(
#             match_msg(r"Dish state set to 'ON'\.", pod="dishmaster1-01-0"),
#             match_msg(
#                 r"E.*Expected <STANDBY> to be equal to <ON>, but was not\.",
#                 section="detail/main",
#             ),
#         )
#     ],
#     "SKBX-025b",
#     "Dish master in state STANDBY after claiming to transition to ON",
#     taints=True,
# )
# add_classifier(
#     [("tests/smoke/test_mvp_clean.py", "test_smell_mvp")],
#     [
#         match_msg(
#             r".*TRANSIENT CORBA system exception: TRANSIENT_ConnectFailed.*",
#             section="detail/main",
#         )
#     ],
#     "SKBX-026",
#     "Tango database not available - incomplete deployment?",
#     taints=True,
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/edit_subarray_resources/test_XR-13_A1.py",
#             "test_allocate_resources",
#         ),
#         (
#             "tests/acceptance/end_uses/maintain_telescope/switch_on_of_controller_elements/test_mvp_start_up.py",
#             "test_start_up",
#         ),
#     ],
#     [
#         match_msg(
#             r".*Timeout .* exceeded on device ska_mid/tm_subarray_node/.*, command On.*",
#             level="ERROR",
#             pod="centralnode-01-0",
#         )
#     ],
#     "SKBX-027",
#     "TM subarray hangs in On()",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/edit_subarray_resources/test_XR-13_A1.py",
#             "test_allocate_resources",
#         ),
#         (
#             "tests/acceptance/end_uses/maintain_telescope/switch_on_of_controller_elements/test_mvp_start_up.py",
#             "test_start_up",
#         ),
#     ],
#     [
#         match_msg(
#             r".*Failed to connect to device ska_mid/tm_subarray_node/1",
#             after_msg_r=r"-> SubarrayNode.On()",
#             level="ERROR",
#             pod="centralnode-01-0",
#         )
#     ],
#     "SKBX-027b",
#     "TM subarray hangs in On()",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/edit_subarray_resources/test_XR-13_A1.py",
#             "test_allocate_resources",
#         ),
#         (
#             "tests/acceptance/end_uses/maintain_telescope/switch_on_of_controller_elements/test_mvp_start_up.py",
#             "test_start_up",
#         ),
#     ],
#     [
#         match_msg(
#             r".*Timeout .* exceeded on device ska_mid/tm_leaf_node/sdp_master, command Standby.*",
#             level="ERROR",
#             pod="centralnode-01-0",
#             section="teardown",
#         )
#     ],
#     "SKBX-027c",
#     "TM SDP master leaf node hangs in Standby() on teardown",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/configure_scan/test_XR-13_A2-Test.py",
#             "test_configure_subarray",
#         )
#     ],
#     [
#         match_msg(
#             r".*Failed to execute read_attribute on device.*", section="detail/main"
#         ),
#         match_msg(
#             r".*Failed to execute read_attribute on device.*",
#             section="teardown_detail/main",
#         ),
#     ],
#     "SKBX-027d",
#     "Failing to read TANGO attribute",
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(
#             r"Error in subscribing Subarray obsState",
#             level="CRITICAL",
#             pod="centralnode-01-0",
#             after_msg_r=r"push_event generated the following python exception:",
#         )
#     ],
#     "SKBX-028",
#     "Central node fails to subscribe to obsState on subarray node",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/run_a_scan/test_XTP-826.py",
#             "test_multi_scan",
#         )
#     ],
#     [
#         match_msg(
#             r"\w*ska\.base\.faults\.StateModelError: Action end_scan_succeeded is not allowed in operational state ON, admin mode 2, observation state 4\..*"
#         )
#     ],
#     "SKBX-029",
#     "Base classes object to end scan callback?",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/configure_scan/test_XR-13_A2-Test.py",
#             "test_configure_subarray",
#         ),
#         (
#             "tests/acceptance/end_uses/conduct_observation/run_a_scan/test_XTP-826.py",
#             "test_multi_scan",
#         ),
#         (
#             "tests/acceptance/end_uses/conduct_observation/run_a_scan/test_XTP-1561.py",
#             "test_scan_id",
#         ),
#     ],
#     [
#         match_msg(
#             r"ska\.base\.faults\.StateModelError: Action end_succeeded is not allowed in operational state ON, admin mode 2, observation state 2.",
#             section="teardown",
#         )
#     ],
#     "SKBX-029b",
#     "Base classes object to end callback in teardown?",
#     taints=True,
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/test_XTP-776_XTP-777-779.py",
#             "test_observing_sbi",
#         )
#     ],
#     [
#         match_msg(
#             r"ska\.base\.faults\.StateModelError: Action end_succeeded is not allowed in operational state ON, admin mode 2, observation state 2."
#         )
#     ],
#     "SKBX-029c",
#     "Base classes object to end callback?",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/maintain_telescope/switch_on_of_controller_elements/test_mvp_start_up.py",
#             "test_start_up",
#         )
#     ],
#     [
#         match_and(
#             match_msg(
#                 "Exiting command StartUpTelescope with return_code ResultCode\.OK.*",
#                 pod="centralnode-01-0",
#             ),
#             match_msg(r".*", missing=True, section="teardown"),
#         )
#     ],
#     "SKBX-030",
#     "test_start_up doesn't get torn down after turning the telescope on",
#     suppresses=["SKBX-015"],
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/monitor_observation/reset_an_aborted_observation/test_XTP-1096.py",
#             "test_subarray_obsreset",
#         ),
#         (
#             "tests/acceptance/end_uses/maintain_subarray/restart_aborted_subarray/test_XTP-1106.py",
#             "test_subarray_restart",
#         ),
#         (
#             "tests/acceptance/end_uses/monitor_observation/test_XTP-1772.py",
#             "test_recovery_from_aborted",
#         ),
#     ],
#     [
#         match_msg(
#             r"Calling ABORT command succeeded.*",
#             missing=True,
#             after_msg_r=r"Exiting command Abort with return_code ResultCode\.STARTED.*",
#         )
#     ],
#     "SKBX-031",
#     "TM subarray node never finishes abort (subelements change obsState too quickly?)",
#     taints=True,
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/run_a_scan/test_XTP-826.py",
#             "test_multi_scan",
#         )
#     ],
#     [
#         match_msg(
#             r"Exception.*while unsubscribing attribute.*This device proxy does not own this subscription.*",
#             device="subarraynode1-sa1-0",
#             section="teardown",
#         )
#     ],
#     "SKBX-032",
#     "TM subarray node never finishes abort (subelements change obsState too quickly?)",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/run_a_scan/test_XTP-1561.py",
#             "test_scan_id",
#         ),
#         (
#             "tests/acceptance/end_uses/conduct_observation/configure_scan/test_XR-13_A2-Test.py",
#             "test_configure_subarray",
#         ),
#         (
#             "tests/acceptance/end_uses/conduct_observation/run_a_scan/test_XTP-826.py",
#             "test_multi_scan",
#         ),
#     ],
#     [match_msg(r"invalid literal for int.*", pod="cbfsubarray01-cbfsubarray-01-0")],
#     "SKBX-033",
#     "CBF subarray complains about delay model not being integer?",
#     harmless=True,
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/configure_scan/test_XR-13_A2-Test.py",
#             "test_configure_subarray",
#         )
#     ],
#     [
#         match_msg(
#             r"errors.*DevError.*The polling \(necessary to send events\) for the attribute pointingstate is not started",
#             pod="subarraynode1-sa1-0",
#         )
#     ],
#     "SKBX-034",
#     "Failure to subscribe to pointingstate, polling not started",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/configure_scan/test_XR-13_A2-Test.py",
#             "test_configure_subarray",
#         )
#     ],
#     [
#         match_msg(
#             r"Finished processing state READY enter callbacks\.",
#             pod="midcspsubarray01-subarray1-0",
#             after_msg_r=r"Finished processing state READY enter callbacks\.",
#             after_msg_attrs=dict(pod="subarraynode1-sa1-0"),
#         )
#     ],
#     "SKB-050",
#     "TMC enters obsState READY ahead of CSP",
# )
# add_classifier(
#     [("tests/smoke/test_logging_namespace.py", "test_logging_namespace")],
#     [match_msg(r"urllib3.exceptions.ConnectTimeoutError.*")],
#     "SKBX-035",
#     "Attempt to access elastic search times out",
# )
# add_classifier(
#     [("tests/smoke/test_logging_namespace.py", "test_logging_namespace")],
#     [match_msg(r"OSError: \[Errno 101\] Network is unreachable")],
#     "SKBX-035b",
#     "Attempt to access elastic search causes 'Network is unreachable'",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/edit_subarray_resources/test_XR-13_A1.py",
#             "test_allocate_resources",
#         )
#     ],
#     [match_msg(r"push_event generated the following python exception:.*")],
#     "SKBX-036",
#     "Spurious 'push_event generated the following Python exception' messages from TM subarray node",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/edit_subarray_resources/test_XR-13_A1.py",
#             "test_allocate_resources",
#         )
#     ],
#     [
#         match_msg(
#             r"               desc = Timeout .* exceeded on device ska_mid/tm_subarray_node/1, command AssignResources"
#         )
#     ],
#     "SKBX-037",
#     "Timeout on AssignResources from TMC central node",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/configure_scan/test_XR-13_A2-Test.py",
#             "test_configure_subarray",
#         )
#     ],
#     [
#         match_and(
#             match_msg(
#                 "Waiting for obsState to transition to READY",
#                 section="detail/Captured stdout call",
#             ),
#             match_msg(
#                 "obsState reached target state READY",
#                 missing=True,
#                 section="detail/Captured stdout call",
#             ),
#             match_msg("E       Failed: Timeout >300.0s", section="detail/main"),
#         )
#     ],
#     "SKBX-038",
#     "TMC gets stuck on transition to READY",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/configure_scan/test_XR-13_A2-Test.py",
#             "test_configure_subarray",
#         ),
#         (
#             "tests/acceptance/end_uses/monitor_observation/test_XTP-1772.py",
#             "test_recovery_from_aborted",
#         ),
#     ],
#     [
#         match_and(
#             match_msg(
#                 "Waiting for obsState to transition to IDLE",
#                 section="detail/Captured stdout call",
#             ),
#             match_msg(
#                 "obsState reached target state IDLE",
#                 missing=True,
#                 section="detail/Captured stdout call",
#             ),
#             match_msg("E       Failed: Timeout >300.0s", section="detail/main"),
#         )
#     ],
#     "SKBX-038b",
#     "TMC gets stuck on transition to IDLE",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/maintain_telescope/switch_on_of_controller_elements/test_XTP-776_XTP-780-781.py",
#             "test_telescope_in_standby",
#         )
#     ],
#     [
#         match_msg(
#             "E       AssertionError: Expected telescope to be ON but instead was OFF",
#             section="detail/main",
#         )
#     ],
#     "SKBX-039",
#     "Central node state is reported as OFF right after turning telescope on",
# )
# add_classifier(
#     [
#         (
#             "tests/smoke/test_validate_device_spec.py",
#             "test_dishmaster_conforms_to_dishmaster_spec",
#         ),
#         (
#             "tests/smoke/test_validate_device_spec.py",
#             "test_dishmaster_conforms_to_tango_wide",
#         ),
#     ],
#     [
#         match_msg(
#             "E           requests.exceptions.HTTPError: 429 Client Error: Too Many Requests for url: .*",
#             section="detail/main",
#         ),
#         match_msg(
#             r"specification_yaml = 'Rate limit exceeded.*", section="detail/main"
#         ),
#     ],
#     "SKBX-040",
#     "GitLab blocks access to device spec due to too many requests",
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(
#             "resources/test_support/oet_helpers.py:2.*: IndexError",
#             section="detail/main",
#         )
#     ],
#     "SKBX-041",
#     "Task index error in OET helpers",
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(
#             "resources/test_support/oet_helpers.py:2.*: AttributeError",
#             section="detail/main",
#         )
#     ],
#     "SKBX-041b",
#     "Task attribute error in OET helpers",
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(
#             "Error in subscribing CSP/SDP Subarray obsState on respective LeafNodes.*",
#             pod="subarraynode1-sa1-0",
#             level="DEBUG",
#         )
#     ],
#     "SKBX-042",
#     "Subarray node fails to subscribe to obsState on leaf nodes",
# )
# add_classifier(
#     [("tests/smoke/test_mvp_clean.py", "test_is_running")],
#     [
#         match_msg(
#             r"\(DevError.*TRANSIENT CORBA system exception: TRANSIENT_CallTimedout.*on device mid_sdp/elt/subarray_1, command On.*",
#             pod="sdpsubarrayleafnode1-01-0",
#             after_msg_r=r"<- SdpSubarrayLeafNode.On.*",
#             after_msg_attrs=dict(pod="sdpsubarrayleafnode1-01-0"),
#         )
#     ],
#     "SKBX-043",
#     "Call timeout on SDP leaf node On() even though call finished",
#     taints=True,
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(
#             r"Logging level set to .* on Python and Tango loggers",
#             pod="sdpsubarrayleafnode1-01-0",
#         )
#     ],
#     "SKBX-044",
#     "SDP subarray leaf node restarts mid-test?",
#     taints=True,
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(
#             r"Logging level set to .* on Python and Tango loggers",
#             pod="cspsubarrayleafnode1-01-0",
#         ),
#         match_msg(
#             r"Logging level set to .* on Python and Tango loggers",
#             pod="cspsubarrayleafnode1-01-0",
#             section="teardown",
#         ),
#     ],
#     "SKBX-044b",
#     "CSP subarray leaf node restarts mid-test?",
#     taints=True,
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(
#             r"Logging level set to .* on Python and Tango loggers",
#             pod="subarraynode1-sa1-0",
#         ),
#         match_msg(
#             r"Logging level set to .* on Python and Tango loggers",
#             pod="subarraynode1-sa1-0",
#             section="teardown",
#         ),
#     ],
#     "SKBX-044c",
#     "Subarray node restarts mid-test?",
#     taints=True,
# )
# add_classifier(
#     [(None, None)],
#     [match_msg(r"Process .* ended with exitcode .*", container="oet-rest")],
#     "SKBX-045",
#     "OET process exits within a test",
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(
#             r"AttributeError: 'NoneType' object has no attribute 'update_resource_deallocation'",
#             pod="centralnode-01-0",
#         )
#     ],
#     "SKBX-046",
#     "resource_manager is None in TMC central node",
#     taints=True,
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/end_uses/conduct_observation/test_XTP-776_XTP-777-779.py",
#             "test_observing_sbi",
#         )
#     ],
#     [
#         match_msg(
#             r".*STATE MONITORING: Expected .* states but recorded .* states",
#             section="detail/Captured stdout call",
#         )
#     ],
#     "SKBX-047",
#     "State monitoring does not see all expected states",
# )
# add_classifier(
#     [(None, None)],
#     [
#         match_msg(
#             r"Exception Shutdown: Cannot stop PID .*: procedure is not running",
#             container="oet-rest",
#         )
#     ],
#     "SKBX-048",
#     "Procedure not running error in OET",
#     taints=True,
# )
# add_classifier(
#     [("tests/smoke/test_validate_bdd_tests.py", "test_validate_bdd_features")],
#     [match_msg(r"E.*AssertionError: Some BDD files not valid", section="detail/main")],
#     "SKBX-049",
#     "Some BDD files not valid",
# )
# add_classifier(
#     [
#         (
#             "tests/acceptance/integration/test_XTP-1079.py",
#             "test_executing_a_transaction_that_fails",
#         )
#     ],
#     [match_status("XFAIL"), match_msg(r".*", missing=True, section="detail/main")],
#     "SKBX-050",
#     "Test transaction_that_fails fails silently",
# )
# add_classifier(
#     [(None, None)],
#     [match_msg(r"E.*KeyError: 'StartUpTelescope'", section="detail/main")],
#     "SKBX-051",
#     "KeyError on StartUpTelescope in TM central node base class",
# )
# add_classifier(
#     [(None, None)],
#     [match_msg(r"KeyError: 'On'", pod="centralnode-01-0")],
#     "SKBX-052",
#     "KeyError on 'On' in TM central node",
#     taints=True,
# )
# add_classifier(
#     [(None, None)],
#     [match_msg(r"KeyError: 'Off'", pod="centralnode-01-0")],
#     "SKBX-052b",
#     "KeyError on 'Off' in TM central node",
#     taints=True,
# )
# add_classifier(
#     [("tests/smoke/test_mvp_clean.py", "test_is_running")],
#     [match_msg(r"It seems some elements are in fault, will attempt to clear them")],
#     "SKBX-053",
#     "Telescope starts up with elements in a FAULT state",
#     taints=True,
# )

# Special pseudo-classifiers
UNKNOWN = Classifier([(None, None)], [], "UNKNOWN", "Unclassified test failure")
UNKNOWN_TD = Classifier(
    [(None, None)], [], "UNKNOWN-TD", "Unclassified teardown failure"
)
TAINT = Classifier([(None, None)], [], "TAINT", "Ignored test failure due to taint")
TAINT_TD = Classifier(
    [(None, None)], [], "TAINT-TD", "Ignored teardown failure due to taint"
)
classifiers += [UNKNOWN, UNKNOWN_TD, TAINT, TAINT_TD]


def classify_test_results(test_results):
    """Run classifiers on test results

    :param test_results: List of test dictionaries
    :returns: List of test/cfr/matched dictionaries with triggered classifiers,
       in the order they were matched
    """

    matches = []

    # Walk through tests
    tainted = False
    tainted_results = 0
    skbs_shown = set()
    skbs_suppressed = set()
    start_time = time.time()
    cfr_time = {cfr.skb: 0 for cfr in classifiers}
    for test in test_results:

        # Check whether we can match it to a classifier
        cfrs = list(classifier_by_test.get((test["file"], test["name"]), []))
        cfrs += classifier_by_test.get((None, None), [])
        cfrs = [cfr for cfr in cfrs if not cfr.only_once or cfr.skb not in skbs_shown]

        # Make messages into a single string for quick scan (see match_msg)
        test["msgs_t"] = "\n\n\n".join(
            "\n".join([f"\n\n#{i}"] + [msg.get(k, "") for k in QUICKSCAN_TAGS])
            for i, msg in enumerate(test["msgs"])
        )

        found_classifier = False
        for cfr in cfrs:
            matched = []
            if cfr.only_once and cfr.skb in skbs_shown:
                continue
            s = time.time()
            if cfr(test, matched) > 0:

                # Decide whether to generate a new trigger
                if not cfr.skb in skbs_suppressed and (
                    not cfr.only_once or cfr.skb not in skbs_shown
                ):

                    matches.append({"test": test, "cfr": cfr, "matched": matched})
                    skbs_shown.add(cfr.skb)

                # Update state - do we see this as a possible cause
                # for thest test failure? Should it be seen as
                # tainting the deployment, therefore invalidating
                # further test failures?
                found_classifier = found_classifier or not cfr.harmless
                tainted = tainted or cfr.taints
                # Check whether this is meant to suppress other messages
                for skb in cfr.suppresses:
                    skbs_suppressed.add(skb)
            cfr_time[cfr.skb] += time.time() - s

        if not found_classifier:
            if (
                test.get("status") not in ["PASSED", "SKIPPED", "XPASS"]
                and not found_classifier
            ):

                # Speculatively point to the last line (which is
                # generally the pytest summary line) as well as all
                # messages with level ERROR or CRITICAL
                msgs = test.get("msgs", [])
                matched = [
                    msg for msg in msgs if msg.get("level") in {"ERROR", "CRITICAL"}
                ]
                matched = matched + test.get("msgs", [])[-1:]

                if tainted:
                    matches.append({"test": test, "cfr": TAINT, "matched": matched})
                else:
                    matches.append({"test": test, "cfr": UNKNOWN, "matched": matched})
            if test.get("teardown_status") in ["ERROR"]:

                # See above
                msgs = test.get("teardown", [])
                matched = [
                    msg for msg in msgs if msg.get("level") in {"ERROR", "CRITICAL"}
                ]
                matched = matched + test.get("msgs", [])[-1:]

                if tainted:
                    matches.append({"test": test, "cfr": TAINT_TD, "matched": matched})
                else:
                    matches.append(
                        {"test": test, "cfr": UNKNOWN_TD, "matched": matched}
                    )

    # Show some timing statistics
    cfr_times = ", ".join(
        f"{skb}: {t:.2f}s"
        for skb, t in sorted(
            cfr_time.items(), key=lambda skb_t: skb_t[1], reverse=True
        )[:3]
    )
    print(
        f"Classifiers evaluated in {time.time()-start_time:.2f} s ({cfr_times})",
        flush=True,
    )
    return matches
