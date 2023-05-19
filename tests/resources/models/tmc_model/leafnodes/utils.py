import functools
import time
from typing import Callable, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


def retry(nr_of_reties: int = 3, wait_time: int = 1):
    @functools.wraps
    def wrapper(command: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return command(*args, **kwargs)
        except Exception:
            nr_of_retries = 0
            exception_to_raise = None
            while nr_of_retries < nr_of_reties:
                time.sleep(wait_time)
                try:
                    return command(*args, **kwargs)
                except Exception as exception:
                    nr_of_retries += 1
                    exception_to_raise = exception
            assert exception_to_raise
            raise exception_to_raise

    return wrapper
