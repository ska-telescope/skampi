"""Creates a global env for a test and test session"""

from typing import TypedDict

from ..obsconfig.config import Observation


class ENV(TypedDict):
    observation: Observation | None


env = ENV(observation=None)


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
