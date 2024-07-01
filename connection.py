import time

from network_enums import *
from ipaddress import IPv4Address, IPv6Address
import socket
from geo_ip_data import get_country, get_asn, get_city
from typing import Union


def get_domain_name(ip_address: Union[IPv4Address, IPv6Address, str]) -> str:
    if not isinstance(ip_address, str):
        ip_address = str(ip_address)
    try:
        domain_name = socket.gethostbyaddr(ip_address)
        return domain_name[0]
    except socket.herror:
        return ip_address + " (Unknown)"


def bps_to_human(bps: float) -> str:
    """
    Convert bits per second to human readable format
    :param bps: Bits per second
    :return: str
    """
    if bps < 1024:
        return f"{bps} bps"
    elif bps < 1024 ** 2:
        return f"{bps / 1024:.3f} Kbps"
    elif bps < 1024 ** 3:
        return f"{bps / 1024 ** 2:.3f} Mbps"
    else:
        return f"{bps / 1024 ** 3:.3f} Gbps"


def get_app_protocol(port, protocol: Protocol) -> str:
    """
    Get the application protocol based on the source and destination ports and the protocol
    :param port: port number
    :param protocol: Protocol number
    :return: str
    """
    try:
        return socket.getservbyport(port, protocol.name)
    except OSError:
        return f"{port} (Unknown)"


class Connection:
    def __init__(self,
                 first_seen: int,
                 last_seen: int,
                 interface_in: str,
                 interface_out: str,
                 src_ip: str,
                 dst_ip: str,
                 src_port: int,
                 dst_port: int,
                 transport_protocol: int,
                 octets: int,
                 packets: int
                 ):
        self.first_seen = first_seen
        self.last_seen = last_seen
        self.interface_in = interface_in
        self.interface_out = interface_out
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.src_port = src_port
        self.dst_port = dst_port
        try:
            self.protocol = Protocol(transport_protocol)
        except ValueError:
            self.protocol = Protocol.unknown
        self.octets = octets
        self.packets = packets

        self.src_data = {}
        self.dst_data = {}
        self.app_protocol = None

        self.finished = False
        self.duration = last_seen - first_seen
        if self.duration > 0:
            self.bps = (octets * 8) / self.duration
        else:
            self.bps = 0
        self.bps_str = None
        self.first_seen_str = None
        self.last_seen_str = None
        self._id = None
        self.is_enriched = False

    def get_id(self):
        if self._id is None:
            self._id = hash((self.interface_in, self.interface_out, self.src_ip, self.dst_ip, self.src_port,
                             self.dst_port, self.protocol))
        return self._id

    def merge(self, new_connection: 'Connection') -> None:
        """
        Update the connection with new information
        """
        if self.get_id() != new_connection.get_id():
            raise ValueError("Cannot merge connections with different IDs")
        if self.finished:
            ValueError("Cannot merge with a finished connection")
        self.last_seen = new_connection.last_seen
        if new_connection.duration > 0:
            self.duration += new_connection.duration
        else:
            self.duration = new_connection.last_seen - self.first_seen
        self.octets += new_connection.octets
        self.packets += new_connection.packets
        if self.duration > 0:
            self.bps = (self.octets * 8) / self.duration
        else:
            self.bps = 0

    def enrich(self):
        """
        Enrich the connection with more information
        """
        if self.is_enriched:
            raise ValueError("Connection is already enriched")
        self.src_data = {
            'country': get_country(self.src_ip),
            # 'city': get_city(self.src_ip),
            # 'asn': get_asn(self.src_ip),
            # 'domain': get_domain_name(self.src_ip),
        }
        self.dst_data = {
            'country': get_country(self.dst_ip),
            # 'city': get_city(self.dst_ip),
            # 'asn': get_asn(self.dst_ip),
            # 'domain': get_domain_name(self.dst_ip),
        }
        self.app_protocol = get_app_protocol(self.dst_port, self.protocol)

        self.bps_str = bps_to_human(self.bps)
        self.first_seen_str = time.ctime(self.first_seen)
        self.last_seen_str = time.ctime(self.last_seen)

        self.is_enriched = True

    def as_dict(self):
        return {
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'interface_in': self.interface_in,
            'interface_out': self.interface_out,
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'src_port': self.src_port,
            'dst_port': self.dst_port,
            'protocol': self.protocol.name,
            'octets': self.octets,
            'packets': self.packets,
            'src_data': self.src_data,
            'dst_data': self.dst_data,
            'app_protocol': self.app_protocol,
            'finished': self.finished,
            'duration': self.duration,
            'bps': self.bps,
            'bps_str': self.bps_str,
            'first_seen_str':  self.first_seen_str,
            'last_seen_str': self.last_seen_str,
        }
