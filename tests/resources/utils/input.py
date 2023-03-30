import json
from pathlib import Path
import yaml
from jsonschema import validate
from typing import NamedTuple, Union, cast
from typing_extensions import TypedDict, NotRequired


class ItemDict(TypedDict):
    dependencies: NotRequired[list[str]]
    platformDependents: NotRequired[list[str]]
    root: NotRequired[Union[bool, None]]


class Item:
    def __init__(
        self,
        name: str,
        dependencies: list[str] = [],
        platformDependents: list[str] = [],
        root: Union[bool, None] = False,
    ) -> None:
        self.name = name
        self._root = root
        self.platform_dependents = platformDependents
        self.dependencies = dependencies

    def is_root(self) -> bool:
        return self._root in [None, True]


def _load():
    schema_path = Path("resources/schemas/diagram.json")
    schema = json.load(schema_path.open())
    diagram_path = Path(("charts/ska-mid/diagram.yaml"))
    diagram = yaml.load((diagram_path.open()), Loader=yaml.Loader)
    validate(diagram, schema)
    diagram = cast(dict[str, ItemDict], diagram)
    graph_items: list[Item] = []
    for item_name, item_values in diagram.items():
        graph_items.append(Item(item_name, **item_values))
    return graph_items


class ValidationError(AssertionError):
    pass


class ItemEdge(NamedTuple):
    start: Item
    end: Item


class DiagramItems:
    def __init__(self) -> None:
        self._graph_items = _load()
        self._start = False
        self._next = self._root

    @property
    def _root(self) -> Item:
        if result := [item for item in self._graph_items if item.is_root()]:
            return result[0]
        raise ValidationError("No root defined in the given data")

    def _get(self, name: str) -> Item:
        if result := [item for item in self._graph_items if item.name == name]:
            return result[0]
        raise ValidationError(f"The referenced dependency {name} has not been defined")

    def _traverse_vertical(self, item: Item):
        for item_name in item.dependencies:
            new_item = self._get(item_name)
            yield new_item
            for inner_item in self._traverse_vertical(new_item):
                yield inner_item

    def _traverse_horizontal(self, item: Item):
        for item_name in item.dependencies:
            new_item = self._get(item_name)
            yield new_item
        for item_name in item.dependencies:
            new_item = self._get(item_name)
            for inner_item in self._traverse_horizontal(new_item):
                yield inner_item

    def _traverse_vertical_edge(self, item: Item):
        for item_name in item.dependencies:
            new_item = self._get(item_name)
            yield ItemEdge(item, new_item)
            for inner_item in self._traverse_vertical_edge(new_item):
                yield inner_item

    def _traverse_horizontal_edge(self, item: Item):
        for item_name in item.dependencies:
            new_item = self._get(item_name)
            yield ItemEdge(item, new_item)
        for item_name in item.dependencies:
            new_item = self._get(item_name)
            for inner_item in self._traverse_horizontal_edge(new_item):
                yield inner_item

    def get_next_item_depth_first(self):
        yield self._root
        for item in self._traverse_vertical(self._root):
            yield item

    def get_next_item_breath_first(self):
        yield self._root
        for item in self._traverse_horizontal(self._root):
            yield item

    def get_next_edge_depth_first(self):
        for item in self._traverse_vertical_edge(self._root):
            yield item

    def get_next_edge_breath_first(self):
        for item in self._traverse_horizontal_edge(self._root):
            yield item
