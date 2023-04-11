from . import data_loading, diagram_building, rendering


def main():
    factory_function = rendering.item_factory_function
    data = data_loading.load(factory_function)
    builder = diagram_building.DiagramBuilder(
        data.graph_items, rendering.diagram_context
    )
    builder.build(f"{data.chart_name:<10}{data.chart_ver}")
