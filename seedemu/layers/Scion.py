from __future__ import annotations
from enum import Enum
from typing import Dict, Tuple, Union

from seedemu.core import (Emulator, Interface, Layer, Network, Registry,
                          Router, ScionAutonomousSystem, ScionRouter,
                          ScopedRegistry, Graphable)
from seedemu.core.ScionAutonomousSystem import IA
from seedemu.layers import ScionBase, ScionIsd


class LinkType(Enum):
    """!
    @brief Type of a SCION link between two ASes.
    """

    ## Core link between core ASes.
    Core = "Core"

    ## Customer-Provider transit link.
    Transit = "Transit"

    ## Non-core AS peering link.
    Peer = "Peer"

    def __str__(self):
        return f"{self.name}"

    def to_topo_format(self) -> str:
        """Return type name as expected in .topo files."""
        if self.value == "Core":
            return "CORE"
        elif self.value == "Transit":
            return "CHILD"
        elif self.value == "Peer":
            return "PEER"
        assert False, "invalid scion link type"

    def to_json(self, a_to_b: bool) -> str:
        if self.value == "Core":
            return "CORE"
        elif self.value == "Peer":
            return "PEER"
        elif self.value == "Transit":
            if a_to_b:
                return "CHILD"
            else:
                return "PARENT"


class Scion(Layer, Graphable):
    """!
    @brief This layer manages SCION inter-AS links.

    This layer requires specifying link end points as ISD-ASN pairs as ASNs
    alone do not uniquely identify a SCION AS (see ScionISD layer).
    """

    __links: Dict[Tuple[IA, IA, str, str, LinkType], int]
    __ix_links: Dict[Tuple[int, IA, IA, str, str, LinkType], int]

    def __init__(self):
        """!
        @brief SCION layer constructor.
        """
        super().__init__()
        self.__links = {}
        self.__ix_links = {}
        self.addDependency('ScionIsd', False, False)

    def getName(self) -> str:
        return "Scion"


    def addXcLink(self, a: Union[IA, Tuple[int, int]], b: Union[IA, Tuple[int, int]],
                  linkType: LinkType, count: int=1, a_router: str="", b_router: str="",) -> 'Scion':
        """!
        @brief Create a direct cross-connect link between to ASes.

        @param a First AS (ISD and ASN).
        @param b Second AS (ISD and ASN).
        @param linkType Link type from a to b.
        @param count Number of parallel links.
        @param a_router router of AS a default is ""
        @param b_router router of AS b default is ""

        @throws AssertionError if link already exists or is link to self.

        @returns self
        """
        a, b = IA(*a), IA(*b)
        assert a.asn != b.asn, "Cannot link as{} to itself.".format(a.asn)
        assert (a, b, a_router, b_router, linkType) not in self.__links, (
            "Link between as{} and as{} of type {} exists already.".format(a, b, linkType))

        self.__links[(a, b, a_router, b_router, linkType)] = count

        return self

    def getXcLinks(self) -> Dict[Tuple[IA, IA, str, str, LinkType], int]:
        """!
        @brief Get all cross-connect links.

        @returns Dictionary of cross-connect links.
        """
        return self.__links

    def addIxLink(self, ix: int, a: Union[IA, Tuple[int, int]], b: Union[IA, Tuple[int, int]],
                  linkType: LinkType, count: int=1, a_router: str="", b_router: str="") -> 'Scion':
        """!
        @brief Create a private link between two ASes at an IX.

        @param ix IXP id.
        @param a First AS (ISD and ASN).
        @param b Second AS (ISD and ASN).
        @param linkType Link type from a to b.
        @param count Number of parallel links.
        @param a_router router of AS a default is ""
        @param b_router router of AS b default is ""

        @throws AssertionError if link already exists or is link to self.

        @returns self
        """
        a, b = IA(*a), IA(*b)
        assert a.asn != b.asn, "Cannot link as{} to itself.".format(a)
        assert (a, b, a_router, b_router, linkType) not in self.__links, (
            "Link between as{} and as{} of type {} at ix{} exists already.".format(a, b, linkType, ix))

        self.__ix_links[(ix, a, b, a_router, b_router, linkType)] = count

        return self

    def getIxLinks(self) -> Dict[Tuple[int, IA, IA, str, str, LinkType], int]:
        """!
        @brief Get all IX links.

        @returns Dictionary of IX links.
        """
        return self.__ix_links

    def configure(self, emulator: Emulator) -> None:
        reg = emulator.getRegistry()
        base_layer: ScionBase = reg.get('seedemu', 'layer', 'Base')
        assert issubclass(base_layer.__class__, ScionBase)

        self._configure_links(reg, base_layer)

    def render(self, emulator: Emulator) -> None:
        pass

    def _doCreateGraphs(self, emulator: Emulator) -> None:
        # core AS: double circle
        # non-core AS: circle
        # core link: bold line
        # transit link: normal line
        # peering link: dashed line

        self._log('Creating SCION graphs...')
        graph = self._addGraph('Scion Connections', False)

        reg = emulator.getRegistry()
        scionIsd_layer: ScionIsd = reg.get('seedemu', 'layer', 'ScionIsd')

        for (a, b, a_router, b_router, rel), count in self.__links.items():
            a_shape = 'doublecircle' if scionIsd_layer.isCoreAs(a.isd, a.asn) else 'circle'
            b_shape = 'doublecircle' if scionIsd_layer.isCoreAs(b.isd, b.asn) else 'circle'

            if not graph.hasVertex('AS{}'.format(a.asn), 'ISD{}'.format(a.isd)):
                graph.addVertex('AS{}'.format(a.asn), 'ISD{}'.format(a.isd), a_shape)
            if not graph.hasVertex('AS{}'.format(b.asn), 'ISD{}'.format(b.isd)):
                graph.addVertex('AS{}'.format(b.asn), 'ISD{}'.format(b.isd), b_shape)

            if rel == LinkType.Core:
                for _ in range(count):
                    graph.addEdge('AS{}'.format(a.asn), 'AS{}'.format(b.asn),
                                'ISD{}'.format(a.isd), 'ISD{}'.format(b.isd),
                                style= 'bold')
            if rel == LinkType.Transit:
                for _ in range(count):
                    graph.addEdge('AS{}'.format(a.asn), 'AS{}'.format(b.asn),
                                'ISD{}'.format(a.isd), 'ISD{}'.format(b.isd),
                                alabel='P', blabel='C')
            if rel == LinkType.Peer:
                for _ in range(count):
                    graph.addEdge('AS{}'.format(a.asn), 'AS{}'.format(b.asn),
                                'ISD{}'.format(a.isd), 'ISD{}'.format(b.isd),
                                style= 'dashed')

        for (ix, a, b, a_router, b_router, rel), count in self.__ix_links.items():
            a_shape = 'doublecircle' if scionIsd_layer.isCoreAs(a.isd, a.asn) else 'circle'
            b_shape = 'doublecircle' if scionIsd_layer.isCoreAs(b.isd, b.asn) else 'circle'

            if not graph.hasVertex('AS{}'.format(a.asn), 'ISD{}'.format(a.isd)):
                graph.addVertex('AS{}'.format(a.asn), 'ISD{}'.format(a.isd), a_shape)
            if not graph.hasVertex('AS{}'.format(b.asn), 'ISD{}'.format(b.isd)):
                graph.addVertex('AS{}'.format(b.asn), 'ISD{}'.format(b.isd), b_shape)

            if rel == LinkType.Core:
                for _ in range(count):
                    graph.addEdge('AS{}'.format(a.asn), 'AS{}'.format(b.asn),
                                'ISD{}'.format(a.isd), 'ISD{}'.format(b.isd),
                                label='IX{}'.format(ix), style= 'bold')
            if rel == LinkType.Transit:
                for _ in range(count):
                    graph.addEdge('AS{}'.format(a.asn), 'AS{}'.format(b.asn),
                                'ISD{}'.format(a.isd), 'ISD{}'.format(b.isd),
                                label='IX{}'.format(ix), alabel='P', blabel='C')
            if rel == LinkType.Peer:
                for _ in range(count):
                    graph.addEdge('AS{}'.format(a.asn), 'AS{}'.format(b.asn),
                                'ISD{}'.format(a.isd), 'ISD{}'.format(b.isd),
                                'IX{}'.format(ix), style= 'dashed')

    def print(self, indent: int = 0) -> str:
        out = ' ' * indent
        out += 'ScionLayer:\n'

        indent += 4
        for (ix, a, b, a_router, b_router, rel), count in self.__ix_links.items():
            out += ' ' * indent
            if a_router == "":
                out += f'IX{ix}: AS{a} -({rel})-> '
            else:
                out += f'IX{ix}: AS{a}_{a_router} -({rel})-> '
            if b_router == "":
                out += f'AS{b}'
            else:
                out += f'AS{b}_{b_router}'
            if count > 1:
                out += f' ({count} times)'
            out += '\n'

        for (a, b, a_router, b_router, rel), count in self.__links.items():
            out += ' ' * indent
            if a_router == "":
                out += f'XC: AS{a} -({rel})-> '
            else:
                out += f'XC: AS{a}_{a_router} -({rel})-> '
            if b_router == "":
                out += f'AS{b}'
            else:
                out += f'AS{b}_{b_router}'
            if count > 1:
                out += f' ({count} times)'
            out += '\n'

        return out

    def _configure_links(self, reg: Registry, base_layer: ScionBase) -> None:
        """Configure SCION links with IFIDs, IPs, ports, etc."""
        # cross-connect links
        for (a, b, a_router, b_router, rel), count in self.__links.items():
            a_reg = ScopedRegistry(str(a.asn), reg)
            b_reg = ScopedRegistry(str(b.asn), reg)
            a_as = base_layer.getAutonomousSystem(a.asn)
            b_as = base_layer.getAutonomousSystem(b.asn)

            if a_router == "" or b_router == "": # if routers are not explicitly specified try to get them
                try:
                    a_router, b_router = self.__get_xc_routers(a.asn, a_reg, b.asn, b_reg)
                except AssertionError:
                    assert False, f"cannot find XC to configure link as{a} --> as{b}"
            else: # if routers are explicitly specified, try to get them
                try:
                    a_router = a_reg.get('rnode', a_router)
                except AssertionError:
                    assert False, f"cannot find router {a_router} in as{a}"
                try:
                    b_router = b_reg.get('rnode', b_router)
                except AssertionError:
                    assert False, f"cannot find router {b_router} in as{b}"

            a_ifaddr, a_net = a_router.getCrossConnect(b.asn, b_router.getName())
            b_ifaddr, b_net = b_router.getCrossConnect(a.asn, a_router.getName())
            assert a_net == b_net
            net = reg.get('xc', 'net', a_net)
            a_addr = str(a_ifaddr.ip)
            b_addr = str(b_ifaddr.ip)

            for _ in range(count):
                self._log(f"add scion XC link: {a_addr} as{a} -({rel})-> {b_addr} as{b}")
                self.__create_link(a_router, b_router, a, b, a_as, b_as,
                                a_addr, b_addr, net, rel)

        # IX links
        for (ix, a, b, a_router, b_router, rel), count in self.__ix_links.items():
            ix_reg = ScopedRegistry('ix', reg)
            a_reg = ScopedRegistry(str(a.asn), reg)
            b_reg = ScopedRegistry(str(b.asn), reg)
            a_as = base_layer.getAutonomousSystem(a.asn)
            b_as = base_layer.getAutonomousSystem(b.asn)

            ix_net = ix_reg.get('net', f'ix{ix}')
            if a_router == "" or b_router == "": # if routers are not explicitly specified get all routers in AS
                a_routers = a_reg.getByType('rnode')
                b_routers = b_reg.getByType('rnode')
            else: # else get the specified routers
                a_routers = [a_reg.get('rnode', a_router)]
                b_routers = [b_reg.get('rnode', b_router)]

            # get the routers connected to the IX
            try:
                a_ixrouter, a_ixif = self.__get_ix_port(a_routers, ix_net)
            except AssertionError:
                assert False, f"cannot resolve scion peering: as{a} not in ix{ix}"
            try:
                b_ixrouter, b_ixif = self.__get_ix_port(b_routers, ix_net)
            except AssertionError:
                assert False, f"cannot resolve scion peering: as{a} not in ix{ix}"

            for _ in range(count):
                self._log(f"add scion IX link: {a_ixif.getAddress()} AS{a} -({rel})->"
                        f"{b_ixif.getAddress()} AS{b}")
                self.__create_link(a_ixrouter, b_ixrouter, a, b, a_as, b_as,
                                str(a_ixif.getAddress()), str(b_ixif.getAddress()),
                                ix_net, rel)

    @staticmethod
    def __get_xc_routers(a: int, a_reg: ScopedRegistry, b: int, b_reg: ScopedRegistry) -> Tuple[Router, Router]:
        """Find routers responsible for a cross-connect link between a and b."""
        for router in a_reg.getByType('rnode'):
            for peer, asn in router.getCrossConnects().keys():
                if asn == b and b_reg.has('rnode', peer):
                    return (router, b_reg.get('rnode', peer))
        assert False

    @staticmethod
    def __get_ix_port(routers: ScopedRegistry, ix_net: Network) -> Tuple[Router, Interface]:
        """Find a router in 'routers' that is connected to 'ix_net' and the
        interface making the connection.
        """
        for router in routers:
            for iface in router.getInterfaces():
                if iface.getNet() == ix_net:
                    return (router, iface)
        else:
            assert False

    def __create_link(self,
                     a_router: ScionRouter, b_router: ScionRouter,
                     a_ia: IA, b_ia: IA,
                     a_as: ScionAutonomousSystem, b_as: ScionAutonomousSystem,
                     a_addr: str, b_addr: str,
                     net: Network, rel: LinkType):
        """Create a link between SCION BRs a and b."""
        a_ifid = a_as.getNextIfid()
        b_ifid = b_as.getNextIfid()
        a_port = a_router.getNextPort()
        b_port = b_router.getNextPort()

        a_iface = {
            "underlay": {
                "public": f"{a_addr}:{a_port}",
                "remote": f"{b_addr}:{b_port}",
            },
            "isd_as": str(b_ia),
            "link_to": rel.to_json(a_to_b=True),
            "mtu": net.getMtu(),
        }

        b_iface = {
            "underlay": {
                "public": f"{b_addr}:{b_port}",
                "remote": f"{a_addr}:{a_port}",
            },
            "isd_as": str(a_ia),
            "link_to": rel.to_json(a_to_b=False),
            "mtu": net.getMtu(),
        }

        # XXX(benthor): Remote interface id could probably be added
        # regardless of LinkType but might then undermine SCION's
        # discovery mechanism of remote interface ids. This way is
        # more conservative: Only add 'remote_interface_id' field to
        # dicts if LinkType is Peer.
        #
        # WARNING: As of February 2023, this feature is not yet
        # supported in upstream SCION.
        if rel == LinkType.Peer:
            self._log("WARNING: As of February 2023 SCION peering links are not supported in upstream SCION")
            a_iface["remote_interface_id"] = b_ifid
            b_iface["remote_interface_id"] = a_ifid

        # Create interfaces in BRs
        a_router.addScionInterface(a_ifid, a_iface)
        b_router.addScionInterface(b_ifid, b_iface)
