import json
from pathlib import Path
from typing import Callable, NamedTuple, cast
from typing_extensions import TypedDict, NotRequired
from jsonschema import validate
from .base import ValidationError, ItemDict, AbstractNodeItem
import yaml


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
    diagram_path = Path(("charts/ska-mid/diagram.yaml"))
    diagram = yaml.load((diagram_path.open()), Loader=yaml.Loader)
    chart_path = Path("charts/ska-mid/Chart.yaml")
    chart = yaml.load((chart_path.open()), Loader=yaml.Loader)
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
        else:
            raise ValidationError(f"Listed chart {item_name} not defined in chart.yaml")
        new_item = factory(item_name, chart_version, item_values)
        graph_items.append(new_item)
    return Data(chart["name"], chart["version"], graph_items)
