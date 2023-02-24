from queue import Empty, Queue
from typing import List, Literal, NamedTuple, Tuple, Union
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.connectors import configuration as con_config
import time


class SourcePosition(NamedTuple):
    ra: float
    dec: float


def get_as_el(target: SourcePosition) -> Tuple[float, float]:
    return (200.0, 60.0)


def point(dish_name: names.DeviceName, desired_az: float, desired_el: float):
    """_summary_

    :param dish: _description_
    :type dish: str
    :param coordinates: _description_
    :type coordinates: Any
    """
    tel = names.TEL()
    assert tel.skamid, "incorrect telescope: Low, this is Mid only"
    dish = con_config.get_device_proxy(dish_name, fast_load=True)
    cmd_time_offset = 5000
    dish.write_attribute(
        "desiredpointing",
        [time.time() * 1000.0 + cmd_time_offset, desired_az, desired_el],
    )

    dish.command_inout("Track", str(time.time() * 1000))


def pointing(
    dish: names.DeviceName,
    inbox: Queue[Union[Literal["Stop"], SourcePosition]],
    target: SourcePosition,
    polling: float = 0.05,
):
    """_summary_

    :param dish_id: _description_
    :type dish_id: str
    :param inbox: _description_
    :param polling: _description_
    :type inbox: Queue
    """
    enabled = True
    while enabled:
        desired_az, desired_el = get_as_el(target)
        point(dish, desired_az, desired_el)
        try:
            incomming_message = inbox.get(timeout=polling)
            if incomming_message == "Stop":
                enabled = False
            if isinstance(incomming_message, SourcePosition):
                target = incomming_message
        except Empty:
            # we ignore empty as an exception but treat it as
            # a flag that poll period has elapsed without any updates
            # thus it will continue with next pointing
            pass


class Pointing:
    """_summary_"""

    def __init__(
        self,
        pool: ThreadPoolExecutor,
        dish: names.DeviceName,
        target: SourcePosition,
        polling: float = 0.05,
    ) -> None:
        """_summary_

        :param dish_id: _description_
        :type dish_id: str
        :param inbox: _description_
        :type inbox: Queue[Union[Literal[&quot;Stop&quot;], Coordinates]]
        :param target: _description_
        :type target: Coordinates
        :param polling: _description_, defaults to 0.05
        :type polling: float, optional
        """
        self._inbox = Queue[Union[Literal["Stop"], SourcePosition]]()
        self._thread = pool.submit(pointing, dish, self._inbox, target, polling)

    def stop(self):
        """_summary_"""
        self._inbox.put("Stop")

    def update_target(self, target: SourcePosition):
        """_summary_

        :param target: _description_
        :type target: Coordinates
        """
        self._inbox.put(target)


@contextmanager
def start_as_cm(
    dishes: list[names.DeviceName],
    target: SourcePosition,
    polling: float = 0.05,
):
    with _start(dishes, target, polling) as pointings:
        yield pointings


def start(
    dishes: list[names.DeviceName], target: SourcePosition, polling: float = 0.05
) -> List[Pointing]:
    """_summary_

    :param the_list: _description_
    :type the_list: list[str]
    :param target: _description_
    :type target: Coordinates
    """
    pool = ThreadPoolExecutor(max_workers=len(dishes))
    return [Pointing(pool, dish, target, polling) for dish in dishes]


@contextmanager
def _start(
    dish_ids: list[names.DeviceName], target: SourcePosition, polling: float = 0.05
):
    """_summary_

    :param the_list: _description_
    :type the_list: list[str]
    :param target: _description_
    :type target: Coordinates
    """
    with ThreadPoolExecutor(max_workers=len(dish_ids)) as pool:
        pointings = [Pointing(pool, dish_id, target, polling) for dish_id in dish_ids]
        yield pointings
        stop(pointings)


def update(pointing_list: list[Pointing], target: SourcePosition):
    """_summary_

    :param pointing_list: _description_
    :type pointing_list: list[Pointing]
    """
    for pointing in pointing_list:
        pointing.update_target(target)


def stop(pointing_list: list[Pointing]):
    """_summary_

    :param pointing_list: _description_
    :type pointing_list: list[Pointing]
    """
    for pointing in pointing_list:
        pointing.stop()
