"""
module containing values for interpreting enumerated values (e.g. ObsState)
"""

import enum


class ObsState(enum.IntEnum):
    """Representation of int ObsState as an Enum."""

    EMPTY = 0
    RESOURCING = 1
    IDLE = 2
    CONFIGURING = 3
    READY = 4
    SCANNING = 5
    ABORTING = 6
    ABORTED = 7
    RESETTING = 8
    FAULT = 9
    RESTARTING = 10
