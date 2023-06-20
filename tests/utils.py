import os


def is_flag_set(env: str) -> bool:
    """
    Checks if a flag is set given an environment variable. It must be set to a
    truthy value
    :param env: Name of the environment variable
    :return: True if the flag is set, False otherwise
    """
    value = os.getenv(env, None)
    if value is None:
        return False

    return value.lower().strip() in ["y", "yes", "t", "true", "1"]
