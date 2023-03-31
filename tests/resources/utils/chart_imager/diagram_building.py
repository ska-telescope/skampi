from contextlib import _GeneratorContextManager, contextmanager
from typing import Callable
from .base import ValidationError, AbstractNodeItem


@contextmanager
def empty_context_manager(diagram_name: str):
    yield


class DiagramBuilder:
    def __init__(
        self,
        graph_items: list[AbstractNodeItem],
        diagram_context: Callable[[str], _GeneratorContextManager[None]] | None,
    ) -> None:
        self._graph_items = graph_items
        self._start = False
        self._next = self._root
        self._diagram_context = (
            empty_context_manager if diagram_context is None else diagram_context
        )

    @property
    def _root(self) -> AbstractNodeItem:
        if result := [item for item in self._graph_items if item.is_root()]:
            return result[0]
        raise ValidationError("No root defined in the given data")

    def _get(self, name: str) -> AbstractNodeItem:
        if result := [item for item in self._graph_items if item.name == name]:
            return result[0]
        raise ValidationError(f"The referenced dependency {name} has not been defined")

    def _traverse_vertical(self, item: AbstractNodeItem):
        for item_name in item.dependencies:
            new_item = self._get(item_name)
            item.connect_to(new_item)
            yield new_item
            for inner_item in self._traverse_vertical(new_item):
                yield inner_item

    def build(self, diagram_name: str):
        with self._diagram_context(diagram_name):
            for _ in self._traverse_vertical(self._root):
                pass
