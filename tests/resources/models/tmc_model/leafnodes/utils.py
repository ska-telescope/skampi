import functools
import time
from typing import Callable, ParamSpec, TypeVar
import logging

T = TypeVar("T")
P = ParamSpec("P")

logger = logging.getLogger(__name__)

def retry(nr_of_reties: int = 3, wait_time: float = 1):
    def wrapper(command: Callable[P, T], ) -> Callable[P, T]:
        def command_with_retry(*args: P.args, **kwargs: P.kwargs):
            try:
                return command(*args, **kwargs)
            except Exception as exception:
                logger.exception(exception.args)
                nr_of_retries = 0
                exception_to_raise = None
                while nr_of_retries < nr_of_reties:
                    time.sleep(wait_time)
                    try: 
                        logger.warning(f"Retrying {command.__repr__()} for {nr_of_retries}th time")
                        return command(*args, **kwargs)
                    except Exception as exception:
                        nr_of_retries += 1
                        exception_to_raise = exception
                assert exception_to_raise
                raise exception_to_raise
        return command_with_retry
    return wrapper





