"""Module that allows for decoupling tango FQDN names by means of specific and
namespaced symbols
"""
import abc
import collections
import logging
from contextlib import contextmanager
from typing import Iterator, List, Tuple, Union, cast

from ska_ser_skallop.utils import env
from ska_ser_skallop.utils.generic_classes import Symbol
from ska_ser_skallop.utils.singleton import Singleton

logger = logging.getLogger(__name__)

SCOPE: Union[str, Tuple[str]] = ("",)


@contextmanager
def set_scope(*scope: str):
    scoped_container = ScopeContainer()
    scoped_container.set_scope(*scope)
    yield
    scoped_container.revert_scope()


class ScopeContainer(metaclass=Singleton):
    def __init__(self) -> None:
        self._stash: List[Union[str, Tuple[str]]] = []

    def set_scope(self, *scope: str):
        global SCOPE
        self._stash.append(SCOPE)
        SCOPE = cast(Tuple[str], scope)

    def revert_scope(self):
        global SCOPE
        stashed = self._stash.pop()
        SCOPE = cast(Tuple[str], stashed)


class DeviceName(Symbol):
    """
    An object that binds additional tag metadata to a particular device FQDN name to
    facilitate searching devices based on categories (tags)
    """

    name: str
    """The actual FQDN for the device
    """
    tags: Tuple
    """a Tuple of tags that applies user defined categories to the name
    """

    def __init__(self, name: str, *tags: str) -> None:
        self.name = name
        self.tags = tags

    def __str__(self) -> str:
        return self.name

    def filter(self, *tags: str) -> Union["DeviceName", None]:
        """checks if the device are within a given set of categories indicated by the tags
        :returns: itself if the deice are within the given tags, otherwise None
        """
        if tags:
            if tags != ("",):
                if any(tag in self.tags for tag in tags):
                    return self
                return None
        return self

    @property
    def enabled(self) -> bool:
        """Whether the device is withing currently set scoped or not.

        :return: True if the device is within the scope.
        """
        if isinstance(SCOPE, str):
            scope = (SCOPE,)
        else:
            scope = SCOPE
        if self.filter(*scope) is None:
            return False
        return True

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, str):
            return self.name == __o
        elif isinstance(__o, Symbol):
            return self.name == __o.__str__()
        else:
            return super().__eq__(__o)

    def __hash__(self):
        print(hash(str(self)))
        return hash(str(self))

    def __ne__(self, __o: object) -> bool:
        if isinstance(__o, str):
            return self.name != __o
        elif isinstance(__o, Symbol):
            return self.name != __o.__str__()
        else:
            return super().__eq__(__o)


class _NameBase:

    _shim = ""

    def _name(self, name: str) -> str:
        return f"{self._shim}{name}"


class FSPSubelement(_NameBase, DeviceName):
    """Represent tango FQDN names for the generic FSP Subelement. The actual FQDN name
    will be determined by the concrete implementation of this class (e.g Correlator or
    PSS)

    e.g.

    .. code-block:: python

        from skallop.connectors.configuration import get_device_proxy
        from skallop.mvp_control.describing import mvp_names

        corr = get_device_proxy(mvp_names.Mid.csp.cbf.fsp(1).correlator)
        pss = get_device_proxy(mvp_names.Mid.csp.cbf.fsp(1).pulsar_search)

    Note that `FSPSubElement` is a `Symbol` class which means you can give the direct
    object to the :py:func:`ska_ser_skallop.connectors.configuration.get_device_proxy` function.

    """

    type = ""
    tags = ("fsp", "csp domain", "cbf domain", "cbf scope")

    def __init__(self, tag: str, index: int) -> None:
        self._shim = tag
        self.index = index
        super().__init__(self._name(f"_{self.type}/{self.index:0>2}"), *self.tags)

    def __str__(self) -> str:
        return self._name(f"_{self.type}/{self.index:0>2}")

    def subarray(self, nr: int) -> DeviceName:
        """Represent the tango FQDN name for the FSP Subelement subarray device
        (namespaced according to the particular concrete implementation)

        .. code-block:: python

            from skallop.connectors.configuration import get_device_proxy
            from skallop.mvp_control.describing import mvp_names

            corr_subarray_1 = get_device_proxy(
                mvp_names.Mid.csp.cbf.fsp(1).correlator.subarray(1)
            )
            pss_subarray_1 = get_device_proxy(
                mvp_names.Mid.csp.cbf.fsp(1).pulsar_search.subarray(1)
            )

        :returns: the subarray name as a DeviceName
        """
        return DeviceName(
            self._name(f"{self.type}subarray/{self.index:0>2}_{nr:0>2}"),
            *{"fsp domain", *self.tags},
        )


class Correlator(FSPSubelement):
    """Represent tango FQDN names for the Correlator FSP Subelement.

    .. code-block:: python

        from skallop.connectors.configuration import get_device_proxy
        from skallop.mvp_control.describing import mvp_names

        device = get_device_proxy(mvp_names.Correlator)

    Note that `Correlator` is a `Symbol` class which means you can give the direct
    object to the :py:func:`ska_ser_skallop.connectors.configuration.get_device_proxy` function.

    """

    type = "corr"

    def __init__(self, tag: str, index: int) -> None:
        self.tags = ("correlator", *self.tags)
        super().__init__(tag, index)


class PSS(FSPSubelement):
    """Represent tango FQDN names for the PSS FSP Subelement.

    .. code-block:: python

        from skallop.connectors.configuration import get_device_proxy
        from skallop.mvp_control.describing import mvp_names

        pss = get_device_proxy(mvp_names.Mid.csp.cbf.fsp(1).pulsar_search)

    Note that `PSS` is a `Symbol` class which means you can give the direct object to
    the :py:func:`ska_ser_skallop.connectors.configuration.get_device_proxy` function.

    """

    type = "pss"

    def __init__(self, tag: str, index: int) -> None:
        self.tags = ("pulsar search", *self.tags)
        super().__init__(tag, index)


class FSP(_NameBase, DeviceName):
    """Represent tango FQDN names for the FSP element.

    e.g.

    .. code-block:: python

        from skallop.connectors.configuration import get_device_proxy
        from skallop.mvp_control.describing import mvp_names

        corr = get_device_proxy(mvp_names.Correlator)
        corr = get_device_proxy(mvp_names.PSS)

    Note that `FSPSubElement` is a `Symbol` class which means you can give the direct
    object to the :py:func:`ska_ser_skallop.connectors.configuration.get_device_proxy` function.

    """

    tags = ("fsp", "cbf scope", "csp scope")

    def __init__(self, tag: str, index: int) -> None:
        self._shim = f"{tag}fsp"
        self._index = index
        self.correlator = Correlator(self._shim, index)
        """Represent tango FQDN names for the Correlator FSP Subelement."""
        self.pulsar_search = PSS(self._shim, index)
        """Represent tango FQDN names for the PSS FSP Subelement."""
        super().__init__(self._name(f"/{self._index:0>2}"), *self.tags)

    def pulsar_timing(self, index: int) -> DeviceName:
        """Represent tango FQDN names for the Pulsar timing FSP Subelement

        .. code-block:: python

            from skallop.connectors.configuration import get_device_proxy
            from skallop.mvp_control.describing import mvp_names

            pss = get_device_proxy(Mid.csp.cbf.fsp(1).pulsar_timing(1))

        :param index: the particular index (or instance) of pulsar search device

        :return: the FQDN name as a DeviceName
        """
        return DeviceName(self._name(f"_pst/{index:0>2}"), *self.tags)

    def vlbi(self, index: int) -> DeviceName:
        """Represent tango FQDN names for the Pulsar timing FSP Subelement

        .. code-block:: python

            from skallop.connectors.configuration import get_device_proxy
            from skallop.mvp_control.describing import mvp_names

            pss = get_device_proxy(Mid.csp.cbf.fsp(1).vlbi(1))

        :param index: the particular index (or instance) of the vlbi device

        :return: the FQDN name as a DeviceName
        """
        return DeviceName(self._name(f"_pst/{index:0>2}"), *self.tags)


class VCC(_NameBase, DeviceName):

    tags = ("vcc", "sensor domain", "cbf scope", "csp scope", "cbf", "csp")
    band_mappings = {1: "12", 2: "3", 3: "4", 4: "5"}

    def __init__(self, tag: str, index: int) -> None:
        self._index = index
        self._shim = f"{tag}vcc"
        super().__init__(self._name(f"/{self._index:0>3}"), *self.tags)

    def __str__(self) -> str:
        return self._name(f"/{self._index:0>3}")

    def sw(self, index: int) -> DeviceName:  # pylint: disable=invalid-name
        """FQDN for VCC switch

        :param index: index representing the VCC switch instance (max 25)

        :return: FQDN for VCC switch as a DeviceName
        """
        return DeviceName(self._name(f"_sw{index}/{self._index:0>3}"), *self.tags)

    def band(self, index: int) -> DeviceName:
        band_nr = self.band_mappings[index]
        assert index < 5, "Only 4 bands currently allowed"
        return DeviceName(self._name(f"_band{band_nr}/{self._index:0>3}"), *self.tags)


class CBF(_NameBase):

    tags = ("cbf scope", "csp scope", "cbf")

    def __init__(self, tag) -> None:
        if tag == "mid":
            self._shim = "mid_csp_cbf/sub_elt/"
            self.controller = DeviceName(self._name("controller"), *self.tags)
        else:
            assert tag == "low"
            self._shim = "low-cbf/"
            self.controller = DeviceName(self._name("control/0"), *self.tags)
        self.tag = tag

    def fsp(self, index: int) -> FSP:
        """FQDN for CBF fsp instance

        :param index: index representing the subarray instance (max 25)

        :return: FQDN for CBF fsp instances
        """
        assert self.tag == "mid", "You requested a low fsp that does not exist"
        return FSP(f"{self.tag}_csp_cbf/", index)

    def subarray(self, index: int) -> DeviceName:
        """FQDN for CBF subarray instance

        :param index: index representing the subarray instance (max 16)

        :return: FQDN for CBF subarray instance
        """
        if self.tag == "mid":
            return DeviceName(
                self._name(f"subarray_{index:0>2}"), *{"fsp domain", *self.tags}
            )
        return DeviceName(
            self._name(f"subarray/{index:0>2}"), *{"fsp domain", *self.tags}
        )

    def vcc(self, index: int) -> VCC:
        """FQDN namespace for VCC for CBF

        :param index: index representing the VCC instance

        :return: FQDN namespace for VCC for CBF
        """
        assert self.tag == "mid", "You requested a low vcc that does not exist"
        return VCC(f"{self.tag}_csp_cbf/", index)

    def allocator(self) -> DeviceName:
        """FQDN for low cbf allocator.

        :return: FQDN for low cbf allocator
        """
        assert self.tag == "low", "You requested a mid allocator that does not exist"
        return DeviceName(self._name("allocator/0"), *{"allocator", *self.tags})


class SDP(_NameBase):

    tags = ("sdp scope", "sdp")

    def __init__(self, tag) -> None:
        self._shim = f"{tag}-sdp"
        self.master = DeviceName(
            self._name("/control/0"), *{"master domain", *self.tags}
        )

    def subarray(self, index: int) -> DeviceName:
        """FQDN for SDP subarray instance

        :param index: index representing the subarray instance (max 16)

        :return: FQDN for SDP subarray instance
        """
        return DeviceName(
            self._name(f"/subarray/{index:0>2}"), *{"sdp domain", *self.tags}
        )


class CSP(_NameBase):

    tags = ("csp scope", "csp")

    def __init__(self, tag) -> None:
        self._shim = f"{tag}-csp"
        self.cbf = CBF(f"{tag}")
        self.controller = DeviceName(
            self._name("/control/0"),
            *{"master domain", "csp controller", *self.tags},
        )

    def subarray(self, index: int) -> DeviceName:
        """FQDN for CSP subarray instance

        param index: index representing the subarray instance (max 16)

        :return: FQDN for CSP subarray instance as a DeviceName
        """
        return DeviceName(self._name(f"/subarray/{index:0>2}"), *self.tags)


# class MCCS(_NameBase):

#     tags = ("mccs scope", "mccs")

#     def __init__(self, tag) -> None:
#         self._shim = f"{tag}-mccs"
#         self.master = DeviceName(
#             self._name("/control/control"),
#             *{"master domain", "mccs master", *self.tags},
#         )

#     def subarray(self, index: int) -> DeviceName:
#         return DeviceName(
#             self._name(f"/subarray/{index:0>2}"), *{"subarrays", *self.tags}
#         )

#     def antenna(self, index: int) -> DeviceName:
#         return DeviceName(
#             self._name(f"/antenna/{index:0>6}"), *{"antennae", *self.tags}
#         )

#     def apiu(self, index: int) -> DeviceName:
#         return DeviceName(self._name(f"/apiu/{index:0>3}"), *{"apius", *self.tags})

#     def beam(self, index: int) -> DeviceName:
#         return DeviceName(self._name(f"/beam/{index:0>3}"), *{"beams", *self.tags})

#     def station(self, index: int) -> DeviceName:
#         return DeviceName(
#             self._name(f"/station/{index:0>3}"), *{"stations", *self.tags}
#         )

#     def subarraybeam(self, index: int) -> DeviceName:
#         return DeviceName(
#             self._name(f"/subarraybeam/{index:0>2}"), *{"subarraybeams", *self.tags}
#         )

#     def subrack(self, index: int) -> DeviceName:
#         return DeviceName(
#             self._name(f"/subrack/{index:0>2}"), *{"subracks", *self.tags}
#         )

#     def tile(self, index: int) -> DeviceName:
#         return DeviceName(self._name(f"/tile/{index:0>4}"), *{"tiles", *self.tags})


class TMSubarrayMid(_NameBase, DeviceName):

    tags = ("tmc scope", "subarrays", "tm")

    def __init__(self, index: int, tag: str) -> None:
        self.index = index
        self._shim = tag
        self.sdp_leaf_node = DeviceName(
            self._name(f"leaf_node/sdp_subarray{self.index:0>2}"),
            *{"leaf nodes", "sdp domain", *self.tags},
        )
        self.csp_leaf_node = DeviceName(
            self._name(f"leaf_node/csp_subarray{self.index:0>2}"),
            *{"leaf nodes", "csp domain", *self.tags},
        )
        super().__init__(self._name(f"subarray_node/{self.index}"), *self.tags)

    @property
    def node(self) -> DeviceName:
        return self


class TMSubarrayLow(_NameBase, DeviceName):

    tags = ("tmc scope", "subarrays", "tm")

    def __init__(self, index: int, tag: str) -> None:
        self.index = index
        self._shim = tag
        self._device_name = DeviceName(
            self._name(f"subarray_node/{self.index}"), *self.tags
        )
        self.sdp_leaf_node = DeviceName(
            self._name(f"leaf_node/sdp_subarray{self.index:0>2}"),
            *{"leaf nodes", "sdp domain", *self.tags},
        )
        self.csp_leaf_node = DeviceName(
            self._name(f"leaf_node/csp_subarray{self.index:0>2}"),
            *{"leaf nodes", "csp domain", *self.tags},
        )
        super().__init__(self._name(f"subarray_node/{self.index}"), *self.tags)


class TMMid(_NameBase):

    tags = ("tmc scope", "tm")

    def __init__(self, tag) -> None:
        self._shim = f"ska_{tag}/tm_"
        self.central_node = DeviceName(
            self._name("central/central_node"), *{"master domain", *self.tags}
        )
        self.sdp_leaf_node = DeviceName(
            self._name("leaf_node/sdp_master"),
            *{"master domain", "leaf nodes", "sdp control", *self.tags},
        )
        self.csp_leaf_node = DeviceName(
            self._name("leaf_node/csp_master"),
            *{"master domain", "leaf nodes", "csp control", *self.tags},
        )

    def dish_leafnode(self, index: int) -> DeviceName:
        """FDQN for TM dish leaf node

        :param index: index representing the instance of the dish leaf node

        :return: FDQN for TM dish leaf node
        """
        return DeviceName(
            self._name(f"leaf_node/d{index:0>4}"),
            *{"sensor domain", "leaf nodes", "dish control", *self.tags},
        )

    def subarray(self, index: int) -> TMSubarrayMid:
        """FDQN for TM subarray node

        :param index: index representing the instance of the subarray node

        :return: FDQN namespace for TM subarray node
        """
        return TMSubarrayMid(index, self._shim)


class TMLow(_NameBase):

    tags = ("tmc scope", "tm")

    def __init__(self, tag) -> None:
        self._shim = f"ska_{tag}/tm_"
        self.central_node = DeviceName(
            self._name("central/central_node"), *{"master domain", *self.tags}
        )
        self.sdp_leaf_node = DeviceName(
            self._name("leaf_node/sdp_master"),
            *{"master domain", "leaf nodes", "sdp control", *self.tags},
        )
        self.csp_leaf_node = DeviceName(
            self._name("leaf_node/csp_master"),
            *{"master domain", "leaf nodes", "csp control", *self.tags},
        )

    def subarray(self, index: int) -> TMSubarrayLow:
        return TMSubarrayLow(index, self._shim)


class Mid(_NameBase):
    """Represents a namespace for containing tango FQDNs in the SKA Mid telescope

    .. code-block:: python

        from skallop.connectors.configuration import get_device_proxy
        from skallop.mvp_control.describing.mvp_names import Mid

        csp = Mid.csp
        sdp = Mid.sdp
        cbf = Mid.csp.cbf
        tm = Mid.tm
        fsp1 = cbf.fsp(1)
        correlator1 = fsp1.correlator
        pulsar_search1 = fsp1.pulsar_search
        subarray1 = tm.subarray(1)

        corr1_sub1 = get_device_proxy(correlator1.subarray(1))
        pss1_sub1 = get_device_proxy(pulsar_search.subarray(1))
        vlbi1 = get_device_proxy(fsp1.vlbi(1))
        csp_master = get_device_proxy(csp.master)
        csp_subarray1 = get_device_proxy(csp.subarray(1))
        cbf_master = get_device_proxy(cbf.master)
        dish1 = get_device_proxy(Mid.dish(1))
        central_node = get_device_proxy(tm.central_node)
        csp_ln = get_device_proxy(tm.csp_leaf_node)
        dish_ln = get_device_proxy(tm.dish_leafnode(1))
        sdp_ln = get_device_proxy(tm.sdp_leaf_node)
        sdp_subarray1_ln = get_device_proxy(subarray1.sdp_leaf_node)
        csp_subarray1_ln = get_device_proxy(subarray1.csp_leaf_node)
        subarray_1 = get_device_proxy(subarray1)
        sdp = get_device_proxy(sdp.master)
        sdp_subarray1 = get_device_proxy(sdp.subarray(1))

    """

    tag = "mid"

    csp = CSP(tag)
    """ SKA Mid csp namespace for tango FQDNs """

    sdp = SDP(tag)
    """ SKA Mid sdp namespace for tango FQDNs """

    tm = TMMid(tag)
    """ SKA Mid tm namespace for tango FQDNs """

    @staticmethod
    def dish(index: int) -> DeviceName:
        """FDQN for SKA Mid Dish

        :param index: index representing the instance of the dish

        :return: FDQN for SKA Mid Dish
        """
        return DeviceName(
            f"{Mid.tag}_d{index:0>4}/elt/master",
            "dishes scope",
            "dishes",
            "sensor domain",
        )

    @staticmethod
    def dishes(ids: List[int]) -> "DomainList":
        """List of FDQNs for SKA Mid Dishes based on input indices.

        :param ids: List of indices representing the instance of the dish

        :returns: List of FDQNs for SKA Mid Dishes
        """
        return DomainList([Mid.dish(id) for id in ids])


class Low(_NameBase):

    tag = "low"

    tm = TMLow(tag)

    sdp = SDP(tag)

    csp = CSP(tag)


def get_tel():
    return TEL()


class DomainList:
    """
    Abstract/generic class that contains a list of :py:class:`DeviceName` objects within
    a particular domain. For example a list of all the dishes. A domain list implements
    a set of basic binary operations on the collective as a whole e.g. :

    .. code-block: python

        # DomainList object containing a list of names =
        # [DeviceName('a1','a'), DeviceName('a2','a'), DeviceName('a3','a')]
        a = A()

        # DomainList object containing  a list of names =
        # [DeviceName('b1','b'), DeviceName('a2','a'), DeviceName('b3','b')]
        b = B()
        c = a + b # new DomainList object containing ['a1', 'a2', 'a3','b1', 'b3']
        for tag, nr_of_occurrences in c.filterables().items():
            print(f"tag:{tag:<10} nr of occurrences:{nr_of_occurrences}")
            # eg tag 'a' occurred 3 times and tag 'b' occurred 2
        c.subtract('a').list # ['b1', 'b3']
        c.filter('a').list # ['a1','a2','a3']
    """

    def __init__(self, token: Union[int, List[DeviceName], None]) -> None:
        self._list: List[DeviceName] = []
        if isinstance(token, int):
            self._generate_list(token)
        elif isinstance(token, list):
            self._list = token
        elif not token:
            self._list = []

    @abc.abstractmethod
    def _generate_list(self, index: int) -> None:
        """"""

    def _get_inner_list(self) -> List[DeviceName]:
        return self._list

    def __getitem__(self, key: int) -> DeviceName:
        return self._list[key]

    def __len__(self) -> int:
        return len(self._list)

    def __add__(self, other: "DomainList") -> "DomainList":
        mutual_exclusive_other = [
            device_name
            for device_name in other._get_inner_list()
            if device_name.name not in self.list
        ]
        new_list = [*self._get_inner_list(), *mutual_exclusive_other]
        new_domain_list = DomainList(0)
        new_domain_list._list = new_list
        return new_domain_list

    def __iter__(self) -> Iterator[DeviceName]:
        output = [item for item in self._list]
        return output.__iter__()

    def filter(self, *tags: str):
        if tags:
            if tags != ("",):
                self._list = [
                    item
                    for item in self._list
                    if any(tag in list(item.tags) for tag in tags)
                ]
        return self

    def filterables(self) -> collections.Counter:
        """
        Generate a summary of tags.

        The summary is a mapping from tag to a frequency count of their
        occurrence; e.g.

        .. code-block: python

            for tag, nr_of_occurrences in domain_list.filterables().items():
                print(f"tag:{tag:<10} nr of occurrences:{nr_of_occurrences}")

        :return: a `Counter` object containing the nr of occurrences for
            each tag
        """
        tags = [tag for item in self._list for tag in item.tags]
        return collections.Counter(tags)

    def subtract(self, tag: str) -> "DomainList":
        """Remove or filter out the set of devices that have a given tag.

        :return: a new `DomainList` object with the devices belonging to the
            given tag removed
        """
        new_list = [item for item in self._list if tag not in list(item.tags)]
        new_domain_list = DomainList(0)
        new_domain_list._list = new_list
        return new_domain_list

    @property
    def list(self) -> List[str]:
        """The list of devices names (excluding their metadata) that this object
        represents. Use this when you want to instantiate a particular device e.g.:

        .. code-block: python

            from skallop.connectors.configuration import get_device_proxy

            for device_name in devices.list:
                device_proxy = get_device_proxy(device_name)
                device_proxy.on()

        :return: a list of device names as FQDN strings
        """
        return [item.name for item in self._list]


def _mid_masters() -> List[DeviceName]:
    return [
        Mid.csp.controller,
        Mid.sdp.master,
        Mid.tm.central_node,
        Mid.tm.csp_leaf_node,
    ]


def _low_masters() -> List[DeviceName]:
    return [
        Low.csp.controller,
        Low.sdp.master,
        Low.tm.central_node,
        Low.tm.csp_leaf_node,
    ]


class Masters(DomainList):
    """A specific implementation of Domain List in that it is used to obtain the device
    names of all the "masters" e.g.

    .. code-block: python

        from skallop.connectors.configuration import get_device_proxy

        for master_name in Masters().list:
            master_device = get_device_proxy(master_name)
            master_device.on()

    """

    def __init__(self) -> None:
        super().__init__(0)
        self._generate_list(0)

    def _generate_list(self, index: int):
        _ = index
        if env.telescope_type_is_mid():
            self._list = _mid_masters()
        elif env.telescope_type_is_low():
            self._list = _low_masters()
        else:
            logger.info("Telescope type is not correct")


class LowMasters(DomainList):
    def __init__(self) -> None:
        super().__init__(0)
        self._generate_list(0)

    def _generate_list(self, index: int):
        _ = index
        self._list = _low_masters()


class MidMasters(DomainList):
    def __init__(self) -> None:
        super().__init__(0)
        self._generate_list(0)

    def _generate_list(self, index: int):
        _ = index
        self._list = _mid_masters()


class Sensors(DomainList):
    """mid only"""

    nr_bands = 4
    nr_switches = 2

    def _generate_list(self, index: int):
        # assert env.telescope_type_is_mid()
        self._list = (
            [
                Mid.dish(index),
                Mid.tm.dish_leafnode(index),
            ]
            + [
                Mid.csp.cbf.vcc(index).band(band)
                for band in range(1, self.nr_bands + 1)
            ]
            + [Mid.csp.cbf.vcc(index).sw(nr) for nr in range(1, self.nr_switches + 1)]
        )


# class MCCSDevices(DomainList):
#     """low only"""

#     nr_antenna = 8
#     nr_apiu = 2
#     nr_beam = 4
#     nr_station = 2
#     nr_subarray_beam = 4
#     nr_tile = 4

#     def _generate_list(self, index: int):
#         assert env.telescope_type_is_low()
#         self._list = (
#             [Low.mccs.antenna(num) for num in range(1, self.nr_antenna + 1)]
#             + [Low.mccs.apiu(num) for num in range(1, self.nr_apiu + 1)]
#             + [Low.mccs.beam(num) for num in range(1, self.nr_beam + 1)]
#             + [Low.mccs.station(num) for num in range(1, self.nr_station + 1)]
#             + [
#                 Low.mccs.subarraybeam(num)
#                 for num in range(1, self.nr_subarray_beam + 1)
#             ]
#             + [Low.mccs.subrack(1)]
#             + [Low.mccs.tile(num) for num in range(1, self.nr_tile + 1)]
#         )


def _skamid_subarrays(nr_of_fsps: int, index: int) -> List[DeviceName]:
    return (
        [
            Mid.tm.subarray(index),
            Mid.tm.subarray(index).csp_leaf_node,
            Mid.tm.subarray(index).sdp_leaf_node,
            Mid.csp.subarray(index),
            Mid.sdp.subarray(index),
        ]
        + [
            Mid.csp.cbf.fsp(j).correlator.subarray(index)
            for j in range(1, nr_of_fsps + 1)
        ]
        + [
            Mid.csp.cbf.fsp(j).pulsar_search.subarray(index)
            for j in range(1, nr_of_fsps + 1)
        ]
    )


def _skalow_subarrays(index: int) -> List[DeviceName]:
    return [
            Low.tm.subarray(index),
            Low.tm.subarray(index).csp_leaf_node,
            Low.tm.subarray(index).sdp_leaf_node,
            Low.csp.subarray(index),
            Low.sdp.subarray(index),
    ]


class SubArrays(DomainList):

    nr_of_fsps = 4

    def _generate_list(self, index: int):
        if env.telescope_type_is_mid():
            self._list = _skamid_subarrays(self.nr_of_fsps, index)
        elif env.telescope_type_is_low():
            self._list = _skalow_subarrays(index)
        else:
            logger.info("Telescope type is not correct")


class MidSubArrays(DomainList):

    nr_of_fsps = 4

    def _generate_list(self, index: int):
        self._list = _skamid_subarrays(self.nr_of_fsps, index)


class LowSubArrays(DomainList):

    nr_of_fsps = 4

    def _generate_list(self, index: int):
        self._list = _skalow_subarrays(index)


class TEL(_NameBase):
    """
    Represents an abstracted namespace for for containing tango FQDNs for a generic
    telescope.
    """

    def __init__(self) -> None:
        if env.telescope_type_is_low():
            tag = "low"
            self.tm = TMLow(tag)
            self.sdp = SDP(tag)
            self.csp = CSP(tag)
            self.skalow = Low()
            self.skamid = None
        else:
            tag = "mid"
            self.csp = CSP(tag)
            self.sdp = SDP(tag)
            self.tm = TMMid(tag)
            self.skalow = None
            self.skamid = Mid()

    def sensors(self, index: int) -> DomainList:
        if self.skamid:
            return Sensors(index)
        return DomainList(None)

    def subarrays(self, index: int) -> DomainList:
        if self.skamid:
            return MidSubArrays(index)
        return LowSubArrays(index)

    def masters(self) -> DomainList:
        if self.skamid:
            return MidMasters()
        return LowMasters()
