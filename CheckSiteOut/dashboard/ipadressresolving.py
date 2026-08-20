import ipaddress
import socket

from dashboard.exceptions import HostUnresolvable


def check_ip_blocked(host):
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise HostUnresolvable(host) from exc

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return True
    return False
