"""Creates a global env for a test and test session"""

from typing import TypedDict

from ..obsconfig.config import Observation


class ENV(TypedDict):
    observation: Observation | None


env = ENV(observation=None)


def get_observation_config(env: ENV) -> Observation:
    if env["observation"] is None:
        env["observation"] = Observation()
    return env["observation"]


def init_observation_config(env: ENV) -> Observation:
    env["observation"] = Observation()
    return env["observation"]
