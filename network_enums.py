from enum import Enum


class Provider(Enum):
    FlowDstPortTotals = 'FlowDstPortTotals'
    FlowInterfaceTotals = 'FlowInterfaceTotals'
    FlowSourceAddrTotals = 'FlowSourceAddrTotals'
    FlowSourceAddrDetails = 'FlowSourceAddrDetails'


class Direction(Enum):
    IN = 'in'
    OUT = 'out'
    BOTH = 'both'


class Protocol(Enum):
    tcp = 6
    udp = 17
    icmp = 1
    igmp = 2
    ospf = 89
    ipv6_icmp = 58
    any = 0
    ipv6_route = 43
    ipv6_frag = 44
    gre = 47
    esp = 50
    ah = 51
    ipv6_no_next_header = 59
    ipv6_dest_options = 60
    ipv6_mobility = 135
    unknown = -1
