import ipaddress
import socket
import logging
from contextlib import contextmanager
from dashboard.exceptions import HostUnresolvable

logger = logging.getLogger(__name__)


def resolve_safe_ip(host):
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
            return None
    return infos[0][4][0]


def check_ip_blocked(host):
    return resolve_safe_ip(host) is None


@contextmanager
def pin_hostname_to_ip(hostname, ip):
    real_getaddrinfo = socket.getaddrinfo

    def pinned_getaddrinfo(host, *args, **kwargs):
        if host == hostname:
            host = ip
        return real_getaddrinfo(host, *args, **kwargs)

    socket.getaddrinfo = pinned_getaddrinfo
    try:
        yield
    finally:
        socket.getaddrinfo = real_getaddrinfo
