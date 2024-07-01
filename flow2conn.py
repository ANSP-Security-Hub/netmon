#!./venv/bin/python3
import json
import sys
sys.path.append('/usr/local/opnsense/scripts/netflow/')

import socket
import time
from lib.parse import parse_flow
from connection import Connection
from cProfile import Profile
from pstats import SortKey, Stats

FLOWD_LOG_FILE = '/var/log/flowd.log'


def flow_addr_byte_to_str(flow_record):
    for key, value in flow_record.items():
        if isinstance(value, bytes):
            if 'addr4' in key:
                flow_record[key] = socket.inet_ntop(socket.AF_INET, value)
            elif 'addr6' in key:
                flow_record[key] = socket.inet_ntop(socket.AF_INET6, value)
            else:
                raise ValueError(f'KEY: {key} is of type bytes! (not compatible with JSON)')
    return flow_record


def get_last_connections(duration_in_seconds, max_hits) -> list[Connection]:
    """
    Get top connections from a provider for a given timeframe\
    :param duration_in_seconds: Duration of the timeframe (seconds) from now to look for connections
    :param max_hits: Maximum number of hits to return
    :return: list
    """
    connections: dict[str, Connection] = {}

    timestamp = int(time.time()) - duration_in_seconds
    print("Getting top connections for the following period:")
    print(f"Start time: {time.ctime(timestamp)}")
    for flow_record in parse_flow(timestamp, FLOWD_LOG_FILE):
        if flow_record is not None:
            flow_record = flow_addr_byte_to_str(flow_record)
            connection = Connection(
                first_seen=flow_record['flow_start'],
                last_seen=flow_record['flow_end'],
                interface_in=flow_record['if_in'],
                interface_out=flow_record['if_out'],
                src_ip=flow_record['src_addr'],
                dst_ip=flow_record['dst_addr'],
                src_port=flow_record['src_port'],
                dst_port=flow_record['dst_port'],
                transport_protocol=flow_record['protocol'],
                octets=flow_record['octets'],
                packets=flow_record['packets']
            )

            if connection.get_id() in connections:
                connections[connection.get_id()].merge(connection)
            else:
                connections[connection.get_id()] = connection

    # sort by octets
    connections_list = list(connections.values())
    print("Connections found:", len(connections_list))
    connections_list.sort(key=lambda c: c.octets, reverse=True)

    return connections_list


def main():
    print("Getting last connections...")
    conns = get_last_connections(60, 2)
    print(f"Found {len(conns)} connections")
    for i, c in enumerate(conns):
        print(f"Enriching connection {i+1}...", end="\r")
        c.enrich()

    print("\nConnections:")
    print(json.dumps([c.as_dict() for c in conns], indent=4))


if __name__ == '__main__':
    with (Profile() as profile):
        main()
        Stats(profile).strip_dirs().sort_stats(SortKey.CALLS).print_stats()



# parse_flow returns a dict with the following keys
# {
#   "recv_time": [
#     1713729856,
#     400109
#   ],
#   "proto_flags_tos": [
#     0,
#     17,
#     0,
#     0
#   ],
#   "agent_addr4": "127.0.0.1",
#   "src_addr4": "10.10.9.3",
#   "dst_addr4": "10.10.10.2",
#   "gateway_addr4": "0.0.0.0",
#   "srcdst_port": [
#     62831,
#     53
#   ],
#   "packets": 1,
#   "octets": 57,
#   "if_indices": [
#     8,
#     2
#   ],
#   "agent_info": [
#     4008000,
#     1713729856,
#     0,
#     9,
#     0
#   ],
#   "flow_times": [
#     3992000,
#     3992000
#   ],
#   "as_info": [
#     0,
#     0,
#     24,
#     24,
#     0
#   ],
#   "recv_sec": 1713729856,
#   "sys_uptime_ms": 4008000,
#   "netflow_ver": 9,
#   "recv": 1713729856,
#   "recv_usec": 400109,
#   "if_ndx_in": 8,
#   "if_ndx_out": 2,
#   "src_port": 62831,
#   "dst_port": 53,
#   "protocol": 17,
#   "tcp_flags": 0,
#   "tos": 0,
#   "flow_start": 1713729840,
#   "flow_finish": 3992000,
#   "agent_addr": "127.0.0.1",
#   "src_addr": "10.10.9.3",
#   "dst_addr": "10.10.10.2",
#   "gateway_addr": "0.0.0.0",
#   "flow_end": 1713729840,
#   "duration_ms": 0,
#   "if_in": "ovpns1",
#   "if_out": "em1"
# }