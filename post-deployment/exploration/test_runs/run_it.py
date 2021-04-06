import pytest
import getopt
import sys
import yaml
from pytest import ExitCode
from functools import reduce
from typing import Tuple
import os


def from_args(argv):
    inputfile = ""
    try:
        opts, args = getopt.getopt(argv, "hf:", ["file="])
    except getopt.GetoptError:
        print("explore_event_subscription.py -f <test specification file>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("explore_event_subscription.py -f <test specification file>")
            sys.exit()
        elif opt in ("-f", "--file"):
            inputfile = arg
    return inputfile


class Test:
    def __init__(self, name, module, group) -> None:
        self.name = name
        self.module = module
        self.group = group
        self.test_path = f"{os.getcwd()}/" f"{group}" f"{module}" f"::{name}"


class TestRun:
    def __init__(self, spec_dict) -> None:
        self.tests = []
        for group in spec_dict.values():
            group_path = get_from_dict(group, "path", default="tests")
            self.runs = get_from_dict(group, "runs", default=1)
            modules = get_from_dict(group, "modules", default="required")
            for module in modules:
                module_path = get_from_dict(module, "path", default="tests")
                tests = get_from_dict(module, "tests", default="required")
                for test_spec in tests:
                    test_name = get_from_dict(test_spec, "name", default="required")
                    test = Test(test_name, module_path, group_path)
                    self.tests.append(test)

    def run_it(self) -> None:
        self.test_outputs = {}
        for i in range(self.runs):
            args = [test.test_path for test in self.tests]
            print(
                f"\n"
                f"*****************************************************"
                f"*************** starting test run {i} ***************"
                f"*****************************************************"
                f"\n"
            )
            output = {}
            result = pytest.main(args)
            output["result"] = result
            self.test_outputs[i] = output
            if self.passed(result):
                continue
            else:
                print("exiting test run as a failure have been generated")
                break
        self.summarise_outputs()

    def passed(self, value) -> bool:
        passed = ExitCode(0)
        return value == passed

    def failed(self, value) -> bool:
        failed = ExitCode(1)
        return value == failed

    def calculate_test_summary(self) -> Tuple[int, int, float, int]:
        output = self.test_outputs.values()
        mapped_passed = [
            output["result"] for output in output if self.passed(output["result"])
        ]
        mapped_failed = [
            output["result"] for output in output if self.failed(output["result"])
        ]
        passed = len(mapped_passed)
        failed = len(mapped_failed)
        passeable = passed + failed
        other = len(output) - passeable
        failure_rate = failed / passeable
        return passed, failed, failure_rate, other

    def summarise_outputs(self) -> None:
        test_passed, test_failed, failure_rate, other = self.calculate_test_summary()
        print(
            f"Nr of tests failed: {test_failed}, "
            f"Nr of tests passed: {test_passed}, "
            f"Failure rate: {failure_rate}, "
            f"Other: {other}"
        )


class SpecFault(Exception):
    pass


def get_from_dict(the_dict, key, default=None, error_message=None):
    if key in the_dict.keys():
        return the_dict[key]
    elif default == "required":
        if error_message == None:
            error_message = f"Error in parsing spec: {key} not specified"
        raise SpecFault(error_message)
    else:
        return default


def main(argv):

    inputfile = from_args(argv)
    with open(inputfile, "r") as file:
        unparsed_spec = yaml.load(file, Loader=yaml.FullLoader)
    spec = TestRun(unparsed_spec)
    spec.run_it()


if __name__ == "__main__":
    main(sys.argv[1:])
