from contextlib import contextmanager
from diagrams import Node, Edge, Diagram, Cluster
from .base import ItemDict, AbstractNodeItem


class NodeItem(AbstractNodeItem):
    def __init__(
        self, item_name: str, chart_version: str, item_values: ItemDict
    ) -> None:
        super().__init__(item_name, chart_version, item_values)
        self._node: None | Node = None
        self.edges: list[Edge] = []

    @property
    def node(self):
        if self._node is None:
            # remove redundant ska-
            name = self.name.replace("ska-", "")
            name += f"\n{self.version}\n"
            name += "\n".join(["" for _ in range(4)])
            self._node = Node(name)
        return self._node

    def connect_to(self, other: "NodeItem"):
        edge = Edge(self.node, forward=True)
        self.node.connect(other.node, edge)
        self.edges.append(edge)


@contextmanager
def diagram_context(diagram_name: str):
    with Diagram("SKA Mid Charts", show=False, direction="TB"):
        with Cluster(diagram_name):
            yield


def item_factory_function(item_name: str, chart_version: str, item_values: ItemDict):
    return NodeItem(item_name, chart_version, item_values)
