from geoip2fast import GeoIP2Fast
from ipaddress import IPv4Address, IPv6Address
from typing import Union

geoip = GeoIP2Fast()


def get_country(ip: Union[IPv4Address, IPv6Address, str]) -> str:
    """
    Get the country of an IP address
    :param ip: IP address
    :return: str
    """
    if not isinstance(ip, str):
        ip = str(ip)

    if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.16."):
        return "Local"

    try:
        res = geoip.lookup(ip).country_code
        if res is None or res in ["", "--"]:
            return "Unknown"
        return res
    except Exception as e:
        return "Unknown"


def get_asn(ip: Union[IPv4Address, IPv6Address, str]) -> str:
    """
    Get the ASN of an IP address
    :param ip: IP address
    :return: str
    """
    if not isinstance(ip, str):
        ip = str(ip)

    if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.16."):
        return "Local"

    try:
        res = geoip.lookup(ip).asn_name
        if res is None or res in ["", "--"]:
            return "Unknown"
        return res
    except Exception as e:
        return "Unknown"


def get_city(ip: Union[IPv4Address, IPv6Address, str]) -> str:
    """
    Get the city of an IP address
    :param ip: IP address
    :return: str
    """
    if not isinstance(ip, str):
        ip = str(ip)

    if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.16."):
        return "Local"

    try:
        res = geoip.lookup(ip).city.name
        if res is None or res in ["", "--"]:
            return "Unknown"
        return res
    except Exception as e:
        return "Unknown"


if __name__ == '__main__':
    myip = "149.200.255.112"
    print(get_country(myip))
    print(get_asn(myip))
    print(get_city(myip))