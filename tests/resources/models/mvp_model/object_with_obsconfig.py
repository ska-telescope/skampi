from .env import get_observation_config


class HasObservation:
    def __init__(self) -> None:
        self.observation = get_observation_config()
