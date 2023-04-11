import logging
import os
import sys
from . import data_loading, diagram_building, rendering


def usage(p_name):
    """Help message."""
    print("Usage:\n\t%s [-v]" % os.path.basename(p_name))
    sys.exit(1)


def main():
    argv = sys.argv
    log_level = logging.WARNING
    if len(argv) == 1:
        pass
    elif len(argv) == 2:
        if argv[1] == "-v":
            log_level = logging.DEBUG
        elif argv[1] in ("-h", "--help"):
            usage(argv[0])
        else:
            logging.error("Unknown parameter %s", argv[1])
            sys.exit(1)
    else:
        logging.error("Unknown parameters %s", ' '.join( argv[1:]))
        sys.exit(1)
    logging.basicConfig(stream=sys.stdout, level=log_level)

    factory_function = rendering.item_factory_function
    data = data_loading.load(factory_function)
    builder = diagram_building.DiagramBuilder(
        data.graph_items, rendering.diagram_context
    )
    builder.build(f"{data.chart_name:<10}{data.chart_ver}")
