from typing import List, NamedTuple, Set, Union
from ska_ser_skallop.event_handling.builders import get_message_board_builder, MessageBoardBuilder

from ska_ser_skallop.mvp_control.describing.mvp_names import DomainList, get_tel


### rule based pre and post conditions ###


## telescope starting up ##
def set_wating_for_start_up(board: MessageBoardBuilder = None) -> MessageBoardBuilder:
    if board:
        brd = board
    else:
        brd = get_message_board_builder()

    nr_of_dishes = 4
    nr_of_subarrays = 1

    tel = get_tel()

    if tel.skamid:
        brd.set_waiting_on(tel.csp.master).for_attribute("state").to_become_equal_to("ON")
        brd.set_waiting_on(tel.sdp.master).for_attribute("state").to_become_equal_to("ON")
        for i in range(1, nr_of_dishes + 1):
            for device in (
                tel.sensors(i).subtract("tm").subtract("vcc")
            ):  # ignore tm leafnodes and vcc
                brd.set_waiting_on(device).for_attribute("state").to_become_equal_to("ON")
                brd.set_waiting_on(tel.skamid.dish(i)).for_attribute("dishmode").to_become_equal_to("OPERATE")
        # subarrays
        for i in range(1, nr_of_subarrays + 1):
            for device in (
                tel.subarrays(i).subtract("tm").subtract("fsp")
            ):  # ignore tm subarrays and fsp
                brd.set_waiting_on(device).for_attribute("state").to_become_equal_to("ON")
    elif tel.skalow:
        brd.set_waiting_on(tel.skalow.mccs.master).for_attribute("state").to_become_equal_to("ON")
        # brd.set_waiting_on(Low.sdp.master).for_attribute("state").to_become_equal_to("ON")
        # ignoring subarrays in low as they don't transition to ON/OFF correctly see skb-95

    return brd


# telescope shutting down
def set_wating_for_shut_down() -> MessageBoardBuilder:
    brd = get_message_board_builder()

    nr_of_dishes = 4
    nr_of_subarrays = 2

    tel = get_tel()

    if tel.skamid:
        brd.set_waiting_on(tel.csp.master).for_attribute("state").to_become_equal_to("STANDBY")
        brd.set_waiting_on(tel.sdp.master).for_attribute("state").to_become_equal_to("OFF")
        for i in range(1, nr_of_dishes + 1):
            for device in (
                tel.sensors(i).subtract("tm").subtract("vcc")
            ):  # ignore tm leafnodes and vcc
                brd.set_waiting_on(device).for_attribute("state").to_become_equal_to("STANDBY")
            brd.set_waiting_on(tel.skamid.dish(i)).for_attribute("dishmode").to_become_equal_to("STANDBY_LP")
        for i in range(1, nr_of_subarrays + 1):
            for device in (
                tel.subarrays(i).subtract("tm").subtract("fsp")
            ):  # ignore tm subarrays and fsp
                brd.set_waiting_on(device).for_attribute("state").to_become_equal_to("OFF")
    elif tel.skalow:
        brd.set_waiting_on(tel.skalow.mccs.master).for_attribute("state").to_become_equal_to("OFF")
        # ignoring subarrays in low as they don't transition to ON/OFF correctly see skb-95

    return brd


# assigning resources


def set_waiting_for_assign_resources(ind: int) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    brd.set_waiting_on(str(tm_subbarray)).for_attribute("obsState").to_become_equal_to("IDLE")
    for device in tel.subarrays(ind).subtract("tm").subtract("cbf domain"):
        brd.set_waiting_on(device).for_attribute("obsState").to_become_equal_to("EMPTY")
    # brd.set_waiting_on(Mid.tm.subarray(ind).sdp_leaf_node).for_attribute('sdpSubarrayObsState').and_observe()
    # brd.set_waiting_on(Mid.tm.subarray(ind).csp_leaf_node).for_attribute('cspSubarrayObsState').and_observe()
    return brd


def set_waiting_until_resourcing(ind: int) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    brd.set_waiting_on(str(tm_subbarray)).for_attribute("obsState").to_become_equal_to(
        "RESOURCING", master=True
    )
    for device in tel.subarrays(ind).subtract("tm").subtract("cbf domain"):
        brd.set_waiting_on(device).for_attribute("obsState").and_observe()
    # brd.set_waiting_on(Mid.tm.subarray(ind).sdp_leaf_node).for_attribute('sdpSubarrayObsState').and_observe()
    # brd.set_waiting_on(Mid.tm.subarray(ind).csp_leaf_node).for_attribute('cspSubarrayObsState').and_observe()
    return brd


def set_waiting_for_release_resources(ind: int) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    brd.set_waiting_on(str(tm_subbarray)).for_attribute("obsState").to_become_equal_to("EMPTY")
    for device in tel.subarrays(ind).subtract("tm").subtract("cbf domain"):
        brd.set_waiting_on(device).for_attribute("obsState").to_become_equal_to("EMPTY")
    # brd.set_waiting_on(Mid.tm.subarray(ind).sdp_leaf_node).for_attribute('sdpSubarrayObsState').and_observe()
    # brd.set_waiting_on(Mid.tm.subarray(ind).csp_leaf_node).for_attribute('cspSubarrayObsState').and_observe()
    # for dishnr in range(1,3):
    # brd.set_waiting_on(f'ska_mid/tm_leaf_node/d{dishnr:04d}').for_attribute('dishPointingState').and_observe()
    #    brd.set_waiting_on(f'mid_d{dishnr:04d}/elt/master').for_attribute('pointingState').and_observe()
    return brd


# configuring subarray


def set_waiting_for_configure_scan(ind: int, receptors: List[int]) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    subarray_change_order = ["CONFIGURING", "READY"]
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    brd.set_waiting_on(str(tm_subbarray)).for_attribute("obsState").to_change_in_order(
        subarray_change_order
    )
    for device in tel.subarrays(ind).subtract("tm").subtract("fsp"):
        brd.set_waiting_on(device).for_attribute("obsState").to_become_equal_to("EMPTY")
    if tel.skamid:
        for index in receptors:
            brd.set_waiting_on(tel.skamid.dish(index)).for_attribute("pointingState").and_observe()
    return brd


def set_waiting_until_configuring(
    ind: int, receptors: List[int]  # pylint: disable=unused-argument
) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    brd.set_waiting_on(str(tm_subbarray)).for_attribute("obsState").to_become_equal_to(
        "CONFIGURING", master=True
    )
    for device in tel.subarrays(ind).subtract("tm").subtract("cbf domain"):
        brd.set_waiting_on(device).for_attribute("obsState").and_observe()
    # brd.set_waiting_on(Mid.tm.subarray(ind).sdp_leaf_node).for_attribute('sdpSubarrayObsState').and_observe()
    # brd.set_waiting_on(Mid.tm.subarray(ind).csp_leaf_node).for_attribute('cspSubarrayObsState').and_observe()
    return brd


def set_waiting_until_scanning(
    ind: int, receptors: List[int]  # pylint: disable=unused-argument
) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    brd.set_waiting_on(str(tm_subbarray)).for_attribute("obsState").to_become_equal_to(
        "SCANNING", master=True
    )
    for device in tel.subarrays(ind).subtract("tm").subtract("cbf domain"):
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
    brd.set_waiting_on(str(tm_subbarray)).for_attribute("obsState").to_become_equal_to("IDLE")
    if tel.skamid:
        brd.set_waiting_on(tel.skamid.csp.cbf.subarray(ind)).for_attribute("obsState").and_observe()
        brd.set_waiting_on(tel.csp.subarray(ind)).for_attribute("obsState").and_observe()
        brd.set_waiting_on(tel.sdp.subarray(ind)).for_attribute("obsState").and_observe()
        for index in receptors:
            brd.set_waiting_on(tel.skamid.dish(index)).for_attribute("pointingState").and_observe()
    return brd


# scanning
def set_waiting_for_scanning_to_complete(ind: int, receptors: List[int]) -> MessageBoardBuilder:

    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    brd.set_waiting_on(str(tm_subbarray)).for_attribute("obsState").to_change_in_order(
        ["SCANNING", "READY"], master=True
    )
    if tel.skamid:
        # brd.set_waiting_on(tel.skamid.csp.cbf.subarray(ind)).for_attribute("obsState").and_observe()
        brd.set_waiting_on(tel.csp.subarray(ind)).for_attribute("obsState").and_observe()
        brd.set_waiting_on(tel.sdp.subarray(ind)).for_attribute("obsState").and_observe()
        for index in receptors:
            brd.set_waiting_on(tel.skamid.dish(index)).for_attribute("pointingState").and_observe()
    return brd


# abort
def set_waiting_for_abort(ind: int, nr_resources: int) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    brd.set_waiting_on(str(tm_subbarray)).for_attribute("obsState").to_change_in_order(
        ["ABORTING", "ABORTED"], master=True
    )
    if tel.skamid:
        # brd.set_waiting_on(tel.skamid.csp.cbf.subarray(ind)).for_attribute("obsState").and_observe()
        brd.set_waiting_on(tel.csp.subarray(ind)).for_attribute("obsState").and_observe()
        brd.set_waiting_on(tel.sdp.subarray(ind)).for_attribute("obsState").and_observe()
        for index in range(1, nr_resources + 1):
            brd.set_waiting_on(tel.skamid.dish(index)).for_attribute("pointingState").and_observe()
    return brd


# obsreset
def set_waiting_for_obsreset(ind: int, receptors: List[int]) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    brd.set_waiting_on(str(tm_subbarray)).for_attribute("obsState").to_change_in_order(
        ["RESETTING", "IDLE"], master=True
    )
    if tel.skamid:
        # brd.set_waiting_on(tel.skamid.csp.cbf.subarray(ind)).for_attribute("obsState").and_observe()
        brd.set_waiting_on(tel.csp.subarray(ind)).for_attribute("obsState").and_observe()
        brd.set_waiting_on(tel.sdp.subarray(ind)).for_attribute("obsState").and_observe()
        for index in receptors:
            brd.set_waiting_on(tel.skamid.dish(index)).for_attribute("pointingState").and_observe()
    return brd


# restart
def set_waiting_for_restart(ind: int, nr_resources: int) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    tel = get_tel()
    tm_subbarray = tel.tm.subarray(ind)
    brd.set_waiting_on(str(tm_subbarray)).for_attribute("obsState").to_change_in_order(
        ["RESTARTING", "EMPTY"], master=True
    )
    if tel.skamid:
        # brd.set_waiting_on(tel.skamid.csp.cbf.subarray(ind)).for_attribute("obsState").and_observe()
        brd.set_waiting_on(tel.csp.subarray(ind)).for_attribute("obsState").and_observe()
        brd.set_waiting_on(tel.sdp.subarray(ind)).for_attribute("obsState").and_observe()
        for index in range(1, nr_resources + 1):
            brd.set_waiting_on(tel.skamid.dish(index)).for_attribute("pointingState").and_observe()
    return brd


class WatchSpec(NamedTuple):
    device_name: str
    attr: str
    value: Union[List[str], str]


def specs(devices: DomainList, attr: str, value: Union[List[str], str]) -> Set[WatchSpec]:
    return {WatchSpec(device_name, attr, value) for device_name in devices}


def set_waiting_for(
    specs: Union[Set[WatchSpec], MessageBoardBuilder]  # pylint: disable=redefined-outer-name
) -> MessageBoardBuilder:
    if isinstance(specs, MessageBoardBuilder):
        return specs
    brd = get_message_board_builder()
    for spec in specs:
        if isinstance(spec.value, str):
            brd.set_waiting_on(spec.device_name).for_attribute(spec.attr).to_become_equal_to(
                spec.value
            )
        else:
            brd.set_waiting_on(spec.device_name).for_attribute(spec.attr).to_change_in_order(
                spec.value
            )
    return brd


def set_observe(
    specs: Set[WatchSpec],  # pylint: disable=redefined-outer-name
) -> MessageBoardBuilder:
    brd = get_message_board_builder()
    for spec in specs:
        brd.set_waiting_on(spec.device_name).for_attribute(spec.attr).and_observe()
    return brd
