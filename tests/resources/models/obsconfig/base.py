import json
import logging
from datetime import datetime
from typing import Any, Callable, Generic, NamedTuple, ParamSpec, TypeVar

from ska_tmc_cdm.schemas import CODEC


class SB(NamedTuple):
    sbi: str
    eb: str
    pb: str


def load_next_sb():
    date = datetime.now()
    unique = (
        f"{date.year}{date.month:02}{date.day:02}" "-" f"{str(int(date.timestamp()*100))[-5:]}"
    )
    sbi = f"sbi-mvp01-{unique}"
    pb = f"pb-mvp01-{unique}"
    eb = f"eb-mvp01-{unique}"
    return SB(sbi, eb, pb)


class SchedulingBlock:
    def __init__(self, *_: Any, **__: Any) -> None:
        logging.info("initialising scheduling block")
        sbi_id, eb_id, pb_id = load_next_sb()
        self.sbi_id = sbi_id
        self.eb_id = eb_id
        self.pb_id = pb_id

    def load_next_sb(self):
        sbi_id, eb_id, pb_id = load_next_sb()
        self.sbi_id = sbi_id
        self.eb_id = eb_id
        self.pb_id = pb_id


T = TypeVar("T")
P = ParamSpec("P")


class EncodedObject(Generic[T]):
    def __init__(self, object_to_encode: T):
        self._object_to_encode = object_to_encode

    @property
    def as_json(self) -> str:
        if isinstance(self._object_to_encode, dict):
            return json.dumps(self._object_to_encode)
        return CODEC.dumps(self._object_to_encode)

    @property
    def as_dict(self) -> dict[Any, Any]:
        return json.loads(self.as_json)

    @property
    def as_object(self) -> T:
        return self._object_to_encode


def encoded(func: Callable[P, T]) -> Callable[P, EncodedObject[T]]:
    def inner(*args: P.args, **kwargs: P.kwargs):
        return EncodedObject(func(*args, **kwargs))

    return inner
