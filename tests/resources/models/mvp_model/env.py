"""Creates a global env for a test and test session"""

from contextlib import contextmanager
from typing import TypedDict

from ..obsconfig.config import Observation


class ENV(TypedDict):
    observation: Observation | None
    previous: list[Observation | None]


env = ENV(observation=None, previous=[])


def get_observation_config() -> Observation:
    # pylint: disable=global-variable-not-assigned
    global env
    if env["observation"] is None:
        env["observation"] = Observation()
    return env["observation"]


def init_observation_config() -> Observation:
    # pylint: disable=global-variable-not-assigned
    global env
    env["observation"] = Observation()
    return env["observation"]


@contextmanager
def interject_observation_config(observation: Observation):
    global env
    env["previous"].append(env["observation"])
    env["observation"] = observation
    yield
    previous = env["previous"].pop()
    env["observation"] = previous
