import json
import logging
from pathlib import Path
from typing import Callable, NamedTuple, cast

import yaml
from jsonschema import validate
from typing_extensions import NotRequired, TypedDict

from .base import AbstractNodeItem, ItemDict, ValidationError


class DependencyDict(TypedDict):
    name: str
    version: str
    condition: NotRequired[str]


class ChartDict(TypedDict):
    name: str
    version: str
    dependencies: list[DependencyDict]


class Data(NamedTuple):
    chart_name: str
    chart_ver: str
    graph_items: list[AbstractNodeItem]


def load(factory: Callable[[str, str, ItemDict], AbstractNodeItem]) -> Data:
    schema_path = Path("resources/schemas/diagram.json")
    schema = json.load(schema_path.open())
    logging.debug("Read schema %s (%d items)", schema_path, len(schema))
    diagram_path = Path(("charts/ska-mid/diagram.yaml"))
    diagram = yaml.load((diagram_path.open()), Loader=yaml.Loader)
    logging.debug("Read diagram %s (%d items)", diagram_path, len(diagram))
    chart_path = Path("charts/ska-mid/Chart.yaml")
    chart = yaml.load((chart_path.open()), Loader=yaml.Loader)
    logging.debug("Read chart %s (%d items)", chart_path, len(chart))
    chart = cast(ChartDict, chart)
    dependencies = chart["dependencies"]
    validate(diagram, schema)
    diagram = cast(dict[str, ItemDict], diagram)
    graph_items: list[AbstractNodeItem] = []
    for item_name, item_values in diagram.items():
        if chart_versions := [
            chart["version"] for chart in dependencies if chart["name"] == item_name
        ]:
            chart_version = chart_versions[0]
            logging.debug("Add item %s version %s", item_name, chart_version)
        else:
            # logging.debug("Listed chart %s not defined in %s", item_name, chart_path)
            raise ValidationError(f"Listed chart {item_name} not defined in {chart_path}")
        new_item = factory(item_name, chart_version, item_values)
        logging.debug("Add %s to graph items", new_item)
        graph_items.append(new_item)
    logging.debug("Loaded %d graph items", len(graph_items))
    return Data(chart["name"], chart["version"], graph_items)
