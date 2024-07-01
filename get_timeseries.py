import sys
sys.path.append('/usr/local/opnsense/scripts/netflow/')

import os
import time
import calendar
import ujson
from lib import load_config
import lib.aggregates

from network_enums import Provider


def get_timeseries(
        provider: Provider,
        start_time: int,
        end_time: int,
        key_fields: str,
        resolution: int
        ) -> dict:
    """
    Get timeseries data from a provider for a given timeframe
    :param provider: Provider to get data from
    :param start_time: Start time of the timeframe (epoch)
    :param end_time: End time of the timeframe (epoch)
    :param key_fields: Fields to group by (comma separated)
    :param resolution: Resolution of the data (seconds)
    :return: dict

    NOTE: This function was ported from the original get_timeseries function in opnsense repo.
    NOTE: The possible values for the key_fields parameters are dependent on the provider:
    - FlowDstPortTotals: 'mtime,last_seen,if,protocol,dst_port,octets,packets'
    - FlowInterfaceTotals: 'mtime,last_seen,if,direction,octets,packets'
    - FlowSourceAddrTotals: 'mtime,last_seen,if,src_addr,direction,octets,packets'
    - FlowSourceAddrDetails: 'mtime,last_seen,if,direction,src_addr,dst_addr,service_port,protocol,octets,packets'

    """
    configuration = load_config()
    timeseries = {}

    dimension_keys = []
    for agg_class in lib.aggregates.get_aggregators():
        if provider == agg_class.__name__:
            obj = agg_class(resolution, database_dir=configuration.database_dir)
            for record in obj.get_timeserie_data(start_time, end_time,
                                                 key_fields.split(',')):
                record_key = []
                for key_field in key_fields.split(','):
                    if key_field in record and record[key_field] is not None:
                        record_key.append(record[key_field])
                    else:
                        record_key.append('')
                record_key = ','.join(record_key)
                start_time_stamp = calendar.timegm(record['start_time'].timetuple())
                if start_time_stamp not in timeseries:
                    timeseries[start_time_stamp] = dict()
                timeseries[start_time_stamp][record_key] = {'octets': record['octets'],
                                                            'packets': record['packets'],
                                                            'resolution': resolution}
                if record_key not in dimension_keys:
                    dimension_keys.append(record_key)

    # When there's no data found, collect keys from the running configuration to render empty results
    if len(dimension_keys) == 0 and os.path.isfile('/usr/local/etc/netflow.conf'):
        tmp = open('/usr/local/etc/netflow.conf').read()
        if tmp.find('netflow_interfaces="') > -1:
            for intf in tmp.split('netflow_interfaces="')[-1].split('"')[0].split():
                dimension_keys.append('%s,in' % intf)
                dimension_keys.append('%s,out' % intf)

    # make sure all timeslices for every dimension key exist (resample collected data)
    start_time = start_time
    while start_time < time.time():
        if start_time not in timeseries:
            timeseries[start_time] = dict()
        for dimension_key in dimension_keys:
            if dimension_key not in timeseries[start_time]:
                timeseries[start_time][dimension_key] = {
                    'octets': 0,
                    'packets': 0,
                    'resolution': resolution
                }
        start_time += resolution

    return timeseries


if __name__ == '__main__':
    result = get_timeseries('FlowInterfaceTotals', 1713171600, 1713182206, 'if,direction', 30)
    print(ujson.dumps(result, indent=4))