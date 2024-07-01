#!./venv/bin/python3
import sys
sys.path.append('/usr/local/opnsense/scripts/netflow/')

import socket
import ujson
import argparse
from datetime import datetime, timedelta
from lib.parse import parse_flow

def flow_addr4_byte_to_str(flow_record):
    for key, value in flow_record.items():
        if isinstance(value, bytes):
            if 'addr4' in key:
                flow_record[key] = socket.inet_ntop(socket.AF_INET, value)
            elif 'addr6' in key:
                flow_record[key] = socket.inet_ntop(socket.AF_INET6, value)
            else:
                raise ValueError(f'KEY: {key} is of type bytes! (not compatible with JSON)')
    return flow_record


def parse_time(time_str):
    if time_str.endswith('h'):
        hours = int(time_str[:-1])
        return int((datetime.now() - timedelta(hours=hours)).timestamp())
    elif time_str.endswith('m'):
        minutes = int(time_str[:-1])
        return int((datetime.now() - timedelta(minutes=minutes)).timestamp())
    elif time_str.endswith('s'):
        seconds = int(time_str[:-1])
        return int((datetime.now() - timedelta(seconds=seconds)).timestamp())
    elif time_str.endswith('d'):
        days = int(time_str[:-1])
        return int((datetime.now() - timedelta(days=days)).timestamp())
    else:
        raise argparse.ArgumentTypeError('Invalid time format. Use h for hours, m for minutes, s for seconds, or d for days.')


def get_timestamp(cmd_args):
    if cmd_args.relative_time:
        return cmd_args.relative_time
    else:
        return cmd_args.timestamp

if __name__ == '__main__':
    # parse arguments and load config
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    parser.add_argument('-p', help='pretty print')
    parser.add_argument('--log', help='flowd log file', default='/var/log/flowd.log')
    group.add_argument('--timestamp', help='start timestamp (epoch)', type=int)
    group.add_argument('--relative-time', help='specify time relative to now (last hour/minute/second/day). Examples: "1h", "15m", "30s", "2d"', type=parse_time, default='1m')
    cmd_args = parser.parse_args()

    timestamp = get_timestamp(cmd_args)
    count = 0
    for flow_record in parse_flow(timestamp, cmd_args.log):
        if flow_record is not None:
            flow_record = flow_addr4_byte_to_str(flow_record)
            count += 1
            #print(count)
            print(ujson.dumps(flow_record, reject_bytes=False))
