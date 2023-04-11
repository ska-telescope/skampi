import logging
from contextlib import AbstractContextManager, contextmanager
from typing import Callable, Generator

from .base import AbstractNodeItem, ValidationError


@contextmanager
def empty_context_manager(diagram_name: str):
    yield


class DiagramBuilder:
    def __init__(
        self,
        graph_items: list[AbstractNodeItem],
        diagram_context: Callable[[str], AbstractContextManager[None]] | None,
    ) -> None:
        self._graph_items = graph_items
        self._start = False
        self._next = self._root
        self._diagram_context = (
            empty_context_manager if diagram_context is None else diagram_context
        )
        
    def __repr__(self) -> str:
        return "(%d items)" % len(self._graph_items)

    @property
    def _root(self) -> AbstractNodeItem:
        if result := [item for item in self._graph_items if item.is_root()]:
            return result[0]
        raise ValidationError("No root defined in the given data")

    def _get(self, name: str) -> AbstractNodeItem:
        if result := [item for item in self._graph_items if item.name == name]:
            return result[0]
        raise ValidationError(f"The referenced dependency {name} has not been defined")

    def _traverse_vertical(
        self, item: AbstractNodeItem
    ) -> Generator[AbstractNodeItem, None, None]:
        for item_name in item.dependencies:
            new_item = self._get(item_name)
            logging.debug("New connection to %s", item_name)
            item.connect_to(new_item)
            yield new_item
            for inner_item in self._traverse_vertical(new_item):
                logging.debug("Connect to %s", inner_item)
                yield inner_item

    def build(self, diagram_name: str):
        with self._diagram_context(diagram_name):
            for _ in self._traverse_vertical(self._root):
                pass
