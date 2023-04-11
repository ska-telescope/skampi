import abc
from typing import Union

from diagrams import Node
from typing_extensions import NotRequired, Self, TypedDict


class ItemDict(TypedDict):
    dependencies: NotRequired[list[str]]
    platformDependents: NotRequired[list[str]]
    root: NotRequired[Union[bool, None]]


class ValidationError(AssertionError):
    pass


class DataItem:
    def __init__(
        self,
        name: str,
        chart_version: str,
        dependencies: list[str] = [],
        platformDependents: list[str] = [],
        root: Union[bool, None] = False,
    ) -> None:
        self.name = name
        self.version = chart_version
        self._root = root
        self.platform_dependents = platformDependents
        self.dependencies = dependencies
        
    def __repr__(self) -> str:
        return "%s" % self.name

    def is_root(self) -> bool:
        return self._root in [None, True]


class AbstractNodeItem(DataItem):
    def __init__(
        self, item_name: str, chart_version: str, item_values: ItemDict
    ) -> None:
        DataItem.__init__(self, item_name, chart_version, **item_values)

    @property
    @abc.abstractmethod
    def node(self) -> Node:
        """"""

    @abc.abstractmethod
    def connect_to(self, other: Self):
        """"""
