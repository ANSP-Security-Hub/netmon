import sys
from typing import Literal

sys.path.append('/usr/local/opnsense/scripts/netflow/')

import time
import lib.aggregates
from lib import load_config

from network_enums import Provider
from utils import log_on_verbose

# define enum for providers


def get_top_usage(
        provider: Provider,
        start_time: int,
        end_time: int,
        key_fields: str,
        value_field: str,
        filter_string: str,
        max_hits: int) -> list[dict]:
    """
    Get top data from a provider for a given timeframe
    :param provider: Provider to get data from
    :param start_time: Start time of the timeframe (epoch)
    :param end_time: End time of the timeframe (epoch)
    :param key_fields: Fields to group by (comma separated)
    :param value_field: Field to aggregate on
    :param filter_string: Filter string to apply (e.g. 'if=1,direction=in')
    :param max_hits: Maximum number of hits to return
    :return: list[dict]

    NOTE: This function was ported from the original get_top_usage function in opnsense repo.
    NOTE: The possible values for the key_fields parameters are dependent on the provider:
    - FlowDstPortTotals: 'mtime,last_seen,if,protocol,dst_port,octets,packets'
    - FlowInterfaceTotals: 'mtime,last_seen,if,direction,octets,packets'
    - FlowSourceAddrTotals: 'mtime,last_seen,if,src_addr,direction,octets,packets'
    - FlowSourceAddrDetails: 'mtime,last_seen,if,direction,src_addr,dst_addr,service_port,protocol,octets,packets'
    """
    MAX_HITS = 100000  # to get all results then filter out the ones outside the timeframe
    result = {}
    configuration = load_config()
    for agg_class in lib.aggregates.get_aggregators():
        if provider.value == agg_class.__name__:
            # provider may specify multiple resolutions, we need to find the one most likely to serve the
            # beginning of our timeframe
            resolutions = sorted(agg_class.resolutions())
            history_per_resolution = agg_class.history_per_resolution()

            selected_resolution = resolutions[-1]
            for resolution in resolutions:
                if (resolution in history_per_resolution and time.time() - history_per_resolution[resolution] <= start_time) or \
                        resolutions[-1] == resolution:
                    selected_resolution = resolution
                    break
            obj = agg_class(selected_resolution, database_dir=configuration.database_dir)
            res = obj.get_top_data(
                start_time=start_time,
                end_time=end_time,
                fields=key_fields.split(','),
                value_field=value_field,
                data_filters=filter_string,
                max_hits=MAX_HITS
            )
            # filter out results with last_seen outside the timeframe
            result = []
            for r in res:
                # 'last_seen' could be int, str, None, not found
                last_seen = r.get('last_seen', -1)
                if isinstance(last_seen, str):
                    if not last_seen.isnumeric():
                        continue
                    last_seen = int(last_seen)

                if start_time <= last_seen <= end_time:
                    result.append(r)
                if len(result) >= max_hits:
                    break
    return result


def get_flow_source_addr_details_all_fields(duration_in_seconds, max_hits,
                                            value: Literal["octets", "packets"] = "octets") -> list[dict]:
    """
    Get top connections from a provider for a given timeframe
    :param duration_in_seconds:
    :param max_hits:
    :param value:
    :return:
    """
    start_time = int(time.time()) - duration_in_seconds
    end_time = int(time.time())
    # print to stderr
    print("Getting top connections for the following period:")
    print(f"Start time: {time.ctime(start_time)}")
    print(f"End time: {time.ctime(end_time)}")
    # time.sleep(3)
    provider = Provider.FlowSourceAddrDetails
    key_fields = "last_seen,if,direction,src_addr,dst_addr,service_port,protocol"

    result = get_top_usage(provider, start_time, end_time, key_fields, value, "", max_hits)

    return result


if __name__ == '__main__':
    # print("FlowDstPortTotals")
    # print(get_top_usage('FlowDstPortTotals', 1713150000, 1713179904, 'dst_port,protocol', 'octets', '', 1))
    # print('FlowSourceAddrTotals')
    # print(get_top_usage('FlowSourceAddrTotals', 1713150000, 1713179904, 'src_addr', 'octets', '', 1))
    # print('FlowInterfaceTotals')
    # print(get_top_usage('FlowInterfaceTotals', 1713150000, 1713179904, 'direction', 'packets', '', 1))
    print('FlowSourceAddrDetails')
    print(get_top_usage(Provider.FlowSourceAddrDetails, 1713150000, 1713179904, 'service_port,protocol,if,src_addr,dst_addr,packets', 'octets', '', 1))