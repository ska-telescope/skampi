from tests.resources.models.obsconfig.config import Observation


def test_it(observation_config: Observation):
    foo = observation_config.target_specs
    foo = "batr"
