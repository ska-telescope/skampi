from typing import List, Union

from ska_ser_skallop.event_handling.builders import (
    MessageBoardBuilder,
    get_message_board_builder,
)
from ska_ser_skallop.mvp_control.describing.mvp_names import get_tel

# rule based pre and post conditions #


# telescope starting up #
def set_wating_for_start_up() -> MessageBoardBuilder:

    brd = get_message_board_builder()

    nr_of_dishes = 4
    nr_of_subarrays = 1

    tel = get_tel()

    if tel.skamid:
        if tel.csp.controller.enabled:
            brd.set_waiting_on(tel.csp.controller).for_attribute(
                "state"
            ).to_become_equal_to("ON", ignore_first=False)
        if tel.sdp.master.enabled:
            brd.set_waiting_on(tel.sdp.master).for_attribute(
                "state"
            ).to_become_equal_to("ON")
        for i in range(1, nr_of_dishes + 1):
            for device in (
                tel.sensors(i).subtract("tm").subtract("vcc")
            ):  # ignore tm leafnodes and vcc
                if device.enabled:
                    brd.set_waiting_on(device).for_attribute(
                        "state"
                    ).to_become_equal_to("ON")
        if tel.csp.cbf.controller.enabled:
            brd.set_waiting_on(tel.csp.cbf.controller).for_attribute(
                "state"
            ).to_become_equal_to("ON")
        # subarrays
        for i in range(1, nr_of_subarrays + 1):
            for device in (
                tel.subarrays(i).subtract("tm").subtract("fsp")
            ):  # ignore tm subarrays and fsp
                if device.enabled:
                    brd.set_waiting_on(device).for_attribute(
                        "state"
                    ).to_become_equal_to("ON")
        if tel.csp.cbf.subarray(1).enabled:
            brd.set_waiting_on(tel.csp.cbf.subarray(1)).for_attribute(
                "state"
            ).to_become_equal_to("ON")
    elif tel.skalow:
        if tel.skalow.mccs.master.enabled:
            brd.set_waiting_on(tel.skalow.mccs.master).for_attribute(
                "state"
            ).to_become_equal_to("ON")
            # brd.set_waiting_on(
            #     Low.sdp.master
            # ).for_attribute("state").to_become_equal_to("ON")
            # TODO SKB-95 ignoring subarrays in low as they don't transition to ON/OFF
            # correctly
        if tel.csp.controller.enabled:
            brd.set_waiting_on(tel.csp.controller).for_attribute(
                "state"
            ).to_become_equal_to("ON", ignore_first=False)
        for i in range(1, 3):
            subarray = tel.csp.subarray(i)
            if subarray.enabled:
                brd.set_waiting_on(subarray).for_attribute("state").to_become_equal_to(
                    "ON", ignore_first=False
                )
        if tel.csp.cbf.controller.enabled:
            brd.set_waiting_on(tel.csp.cbf.controller).for_attribute(
                "state"
            ).to_become_equal_to("ON", ignore_first=False)
        # only wait for subarray 1
        if tel.csp.cbf.subarray(1).enabled:
            brd.set_waiting_on(tel.csp.cbf.subarray(1)).for_attribute(
                "state"
            ).to_become_equal_to("ON", ignore_first=False)
        if tel.skalow.sdp.master.enabled:
            brd.set_waiting_on(tel.sdp.master).for_attribute(
                "state"
            ).to_become_equal_to("ON")
        if tel.skalow.mccs.master.enabled:
            brd.set_waiting_on(tel.skalow.mccs.master).for_attribute(
                "state"
            ).to_become_equal_to("ON", ignore_first=False)
    return brd


# telescope shutting down
def set_wating_for_shut_down() -> MessageBoardBuilder:
    brd = get_message_board_builder()

    nr_of_dishes = 4
    nr_of_subarrays = 1

    tel = get_tel()

    if tel.skamid:
        if tel.csp.controller.enabled:
            brd.set_waiting_on(tel.csp.controller).for_attribute(
                "state"
            ).to_become_equal_to("STANDBY", ignore_first=False)
        if tel.sdp.master.enabled:
            brd.set_waiting_on(tel.sdp.master).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
        for i in range(1, nr_of_dishes + 1):
            for device in (
                tel.sensors(i).subtract("tm").subtract("vcc")
            ):  # ignore tm leafnodes and vcc
                if device.enabled:
                    brd.set_waiting_on(device).for_attribute(
                        "state"
                    ).to_become_equal_to("STANDBY", ignore_first=False)
        if tel.csp.cbf.controller.enabled:
            brd.set_waiting_on(tel.csp.cbf.controller).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
        for i in range(1, nr_of_subarrays + 1):
            for device in (
                tel.subarrays(i).subtract("tm").subtract("fsp")
            ):  # ignore tm subarrays and fsp
                if device.enabled:
                    brd.set_waiting_on(device).for_attribute(
                        "state"
                    ).to_become_equal_to("OFF", ignore_first=False)
        if tel.csp.cbf.subarray(1).enabled:
            brd.set_waiting_on(tel.csp.cbf.subarray(1)).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
    elif tel.skalow:
        if tel.csp.controller.enabled:
            brd.set_waiting_on(tel.csp.controller).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
        for i in range(1, nr_of_subarrays + 1):
            subarray = tel.csp.subarray(i)
            if subarray.enabled:
                brd.set_waiting_on(subarray).for_attribute("state").to_become_equal_to(
                    "OFF", ignore_first=False
                )
        if tel.csp.cbf.controller.enabled:
            brd.set_waiting_on(tel.csp.cbf.controller).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
        # only wait for subarray 1
        if tel.csp.cbf.subarray(1).enabled:
            brd.set_waiting_on(tel.csp.cbf.subarray(1)).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
        if tel.skalow.sdp.master.enabled:
            brd.set_waiting_on(tel.sdp.master).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
        if tel.skalow.mccs.master.enabled:
            brd.set_waiting_on(tel.skalow.mccs.master).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
    return brd


# assigning resources


def set_waiting_for_assign_resources(ind: int) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    if tm_subbarray.enabled:
        brd.set_waiting_on(str(tm_subbarray)).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")
    for device in tel.subarrays(ind).subtract("tm").subtract("cbf domain"):
        if device.enabled:
            brd.set_waiting_on(device).for_attribute("obsState").to_become_equal_to(
                "IDLE"
            )
    # brd.set_waiting_on(
    #     Mid.tm.subarray(ind).sdp_leaf_node
    # ).for_attribute('sdpSubarrayObsState').and_observe()
    # brd.set_waiting_on(
    #     Mid.tm.subarray(ind).csp_leaf_node
    # ).for_attribute('cspSubarrayObsState').and_observe()
    return brd


def set_waiting_until_resourcing(ind: int) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    if tm_subbarray.enabled:
        brd.set_waiting_on(str(tm_subbarray)).for_attribute(
            "obsState"
        ).to_become_equal_to("RESOURCING", master=True)
    for device in tel.subarrays(ind).subtract("tm").subtract("cbf domain"):
        if device.enabled:
            brd.set_waiting_on(device).for_attribute("obsState").and_observe()
    # brd.set_waiting_on(Mid.tm.subarray(ind).sdp_leaf_node).for_attribute('sdpSubarrayObsState').and_observe()
    # brd.set_waiting_on(Mid.tm.subarray(ind).csp_leaf_node).for_attribute('cspSubarrayObsState').and_observe()
    return brd


def set_waiting_for_release_resources(ind: int) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    if tm_subbarray.enabled:
        brd.set_waiting_on(str(tm_subbarray)).for_attribute(
            "obsState"
        ).to_become_equal_to("EMPTY")
    for device in tel.subarrays(ind).subtract("tm").subtract("cbf domain"):
        if device.enabled:
            brd.set_waiting_on(device).for_attribute("obsState").to_become_equal_to(
                "EMPTY"
            )
    # brd.set_waiting_on(Mid.tm.subarray(ind).sdp_leaf_node).for_attribute('sdpSubarrayObsState').and_observe()
    # brd.set_waiting_on(Mid.tm.subarray(ind).csp_leaf_node).for_attribute('cspSubarrayObsState').and_observe()
    # for dishnr in range(1,3):
    # brd.set_waiting_on(f'ska_mid/tm_leaf_node/d{dishnr:04d}').for_attribute('dishPointingState').and_observe()
    #    brd.set_waiting_on(f'mid_d{dishnr:04d}/elt/master').for_attribute('pointingState').and_observe()
    return brd


# configuring subarray


def set_waiting_for_configure_scan(
    ind: int, receptors: List[int]
) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    subarray_change_order = ["CONFIGURING", "READY"]
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    if tm_subbarray.enabled:
        brd.set_waiting_on(str(tm_subbarray)).for_attribute(
            "obsState"
        ).to_change_in_order(subarray_change_order)
    for device in tel.subarrays(ind).subtract("tm").subtract("fsp"):
        if device.enabled:
            brd.set_waiting_on(device).for_attribute("obsState").to_become_equal_to(
                "EMPTY"
            )
    if tel.skamid:
        for index in receptors:
            if tel.skamid.dish(index).enabled:
                brd.set_waiting_on(tel.skamid.dish(index)).for_attribute(
                    "pointingState"
                ).and_observe()
    return brd


def set_waiting_until_configuring(
    ind: int, receptors: List[int]
) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    if tm_subbarray.enabled:
        brd.set_waiting_on(str(tm_subbarray)).for_attribute(
            "obsState"
        ).to_become_equal_to("CONFIGURING", master=True)
    for device in tel.subarrays(ind).subtract("tm").subtract("cbf domain"):
        if device.enabled:
            brd.set_waiting_on(device).for_attribute("obsState").and_observe()
    # brd.set_waiting_on(Mid.tm.subarray(ind).sdp_leaf_node).for_attribute('sdpSubarrayObsState').and_observe()
    # brd.set_waiting_on(Mid.tm.subarray(ind).csp_leaf_node).for_attribute('cspSubarrayObsState').and_observe()
    return brd


def set_waiting_until_scanning(ind: int, receptors: List[int]) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    if tm_subbarray.enabled:
        brd.set_waiting_on(str(tm_subbarray)).for_attribute(
            "obsState"
        ).to_become_equal_to("SCANNING", master=True)
    for device in tel.subarrays(ind).subtract("tm").subtract("cbf domain"):
        if device.enabled:
            brd.set_waiting_on(device).for_attribute("obsState").and_observe()
    # brd.set_waiting_on(Mid.tm.subarray(ind).sdp_leaf_node).for_attribute('sdpSubarrayObsState').and_observe()
    # brd.set_waiting_on(Mid.tm.subarray(ind).csp_leaf_node).for_attribute('cspSubarrayObsState').and_observe()
    return brd


def set_waiting_for_releasing_a_configuration(
    ind: int, receptors: List[int]
) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    if tm_subbarray.enabled:
        brd.set_waiting_on(str(tm_subbarray)).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")
    if tel.skamid:
        if tel.skamid.csp.cbf.subarray(ind).enabled:
            brd.set_waiting_on(tel.skamid.csp.cbf.subarray(ind)).for_attribute(
                "obsState"
            ).and_observe()
        if tel.csp.subarray(ind).enabled:
            brd.set_waiting_on(tel.csp.subarray(ind)).for_attribute(
                "obsState"
            ).and_observe()
        if tel.sdp.subarray(ind).enabled:
            brd.set_waiting_on(tel.sdp.subarray(ind)).for_attribute(
                "obsState"
            ).and_observe()
        for index in receptors:
            if tel.skamid.dish(index).enabled:
                brd.set_waiting_on(tel.skamid.dish(index)).for_attribute(
                    "pointingState"
                ).and_observe()
    return brd


# scanning
def set_waiting_for_scanning_to_complete(
    ind: int, receptors: List[int]
) -> MessageBoardBuilder:

    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    if tm_subbarray.enabled:
        brd.set_waiting_on(str(tm_subbarray)).for_attribute(
            "obsState"
        ).to_change_in_order(["SCANNING", "READY"], master=True)
    if tel.skamid:
        # brd.set_waiting_on(tel.skamid.csp.cbf.subarray(ind)).for_attribute("obsState").and_observe()
        if tel.csp.subarray(ind).enabled:
            brd.set_waiting_on(tel.csp.subarray(ind)).for_attribute(
                "obsState"
            ).and_observe()
        if tel.sdp.subarray(ind).enabled:
            brd.set_waiting_on(tel.sdp.subarray(ind)).for_attribute(
                "obsState"
            ).and_observe()
        for index in receptors:
            if tel.skamid.dish(index).enabled:
                brd.set_waiting_on(tel.skamid.dish(index)).for_attribute(
                    "pointingState"
                ).and_observe()
    return brd


# abort
def set_waiting_for_abort(ind: int, nr_resources: int) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    if tm_subbarray.enabled:
        brd.set_waiting_on(str(tm_subbarray)).for_attribute(
            "obsState"
        ).to_change_in_order(["ABORTING", "ABORTED"], master=True)
    if tel.skamid:
        # brd.set_waiting_on(tel.skamid.csp.cbf.subarray(ind)).for_attribute("obsState").and_observe()
        if tel.csp.subarray(ind).enabled:
            brd.set_waiting_on(tel.csp.subarray(ind)).for_attribute(
                "obsState"
            ).and_observe()
        if tel.sdp.subarray(ind).enabled:
            brd.set_waiting_on(tel.sdp.subarray(ind)).for_attribute(
                "obsState"
            ).and_observe()
        for index in range(1, nr_resources + 1):
            if tel.skamid.dish(index).enabled:
                brd.set_waiting_on(tel.skamid.dish(index)).for_attribute(
                    "pointingState"
                ).and_observe()
    return brd


# obsreset
def set_waiting_for_obsreset(ind: int, receptors: List[int]) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    if tm_subbarray.enabled:
        brd.set_waiting_on(str(tm_subbarray)).for_attribute(
            "obsState"
        ).to_change_in_order(["RESETTING", "IDLE"], master=True)
    if tel.skamid:
        # brd.set_waiting_on(tel.skamid.csp.cbf.subarray(ind)).for_attribute("obsState").and_observe()
        if tel.csp.subarray(ind).enabled:
            brd.set_waiting_on(tel.csp.subarray(ind)).for_attribute(
                "obsState"
            ).and_observe()
        if tel.sdp.subarray(ind).enabled:
            brd.set_waiting_on(tel.sdp.subarray(ind)).for_attribute(
                "obsState"
            ).and_observe()
        for index in receptors:
            if tel.skamid.dish(index).enabled:
                brd.set_waiting_on(tel.skamid.dish(index)).for_attribute(
                    "pointingState"
                ).and_observe()
    return brd


# restart
def set_waiting_for_restart(ind: int, nr_resources: int) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    if tm_subbarray.enabled:
        brd.set_waiting_on(str(tm_subbarray)).for_attribute(
            "obsState"
        ).to_change_in_order(["RESTARTING", "EMPTY"], master=True)
    if tel.skamid:
        # brd.set_waiting_on(tel.skamid.csp.cbf.subarray(ind)).for_attribute("obsState").and_observe()
        if tel.csp.subarray(ind).enabled:
            brd.set_waiting_on(tel.csp.subarray(ind)).for_attribute(
                "obsState"
            ).and_observe()
        if tel.sdp.subarray(ind).enabled:
            brd.set_waiting_on(tel.sdp.subarray(ind)).for_attribute(
                "obsState"
            ).and_observe()
        for index in range(1, nr_resources + 1):
            if tel.skamid.dish(index).enabled:
                brd.set_waiting_on(tel.skamid.dish(index)).for_attribute(
                    "pointingState"
                ).and_observe()
    return brd
