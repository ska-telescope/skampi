import logging
from diagrams import Diagram
from diagrams.k8s.ecosystem import Helm
from diagrams import Node
from .input import DiagramItems


def test_it():
    for item in DiagramItems().get_next_item_depth_first():
        logging.info(item.name)

    for item in DiagramItems().get_next_item_breath_first():
        logging.info(item.name)

    for edge in DiagramItems().get_next_edge_depth_first():
        logging.info(f"{edge.start.name}-------->{edge.end.name}")

    for edge in DiagramItems().get_next_edge_breath_first():
        logging.info(f"{edge.start.name}-------->{edge.end.name}")


def main():
    diagram = DiagramItems()
    test_it()
    with Diagram("First try", show=False):
        branch: None | Node = None
        for item in diagram.get_next_item_depth_first():
            if branch:
                next_node = Helm(item.name)
                branch >> next_node
                branch = next_node
            else:
                branch = Helm(item.name)
