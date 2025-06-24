import threading
import os, socket, uuid

_agent_id = None
_agent_id_lock = threading.Lock()

def get_agent_id():
    global _agent_id
    if _agent_id is None:
        with _agent_id_lock:
            if _agent_id is None:
                _agent_id = (os.getenv("DASHCORN_AGENT_ID") or
                    f"{socket.gethostname()}{decorate_mac(get_mac_address())}")
    return _agent_id

import psutil

def get_mac_address(preferred_interfaces=("eth0", "en0", "wlan0")):
    for iface in preferred_interfaces:
        addrs = psutil.net_if_addrs().get(iface)
        if addrs:
            for addr in addrs:
                if addr.family == psutil.AF_LINK:
                    return addr.address
    return None

def decorate_mac(mac_str, prefix_with: str = "-"):
    if mac_str is None:
        return ""
    return prefix_with + mac_str.replace(":", "")
