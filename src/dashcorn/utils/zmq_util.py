import os
import zmq
import errno
import stat

from typing import Literal, Optional

Protocol = Literal["ipc", "tcp"]

def renew_zmq_ipc_socket(ipc_path: str, protocol: Optional[Protocol] = None, strict: bool = True):
    """
    Safely binds a zmq socket to the given ipc path.
    If the file already exists, attempts to remove it before binding.

    :param ipc_path: The file system path (e.g., '/tmp/mysocket') for ipc:// binding
    :param strict: If True, only remove the file if it's a socket file
    """
    if protocol == "ipc" and ipc_path and os.path.exists(ipc_path):
        try:
            if strict:
                mode = os.stat(ipc_path).st_mode
                if not stat.S_ISSOCK(mode):
                    raise RuntimeError(f"Refusing to remove non-socket file: {ipc_path}")
            os.remove(ipc_path)
        except OSError as e:
            if e.errno == errno.EBUSY:
                raise RuntimeError(f"Cannot remove busy socket file: {ipc_path}")
            else:
                raise RuntimeError(f"Failed to remove existing file {ipc_path}: {e}")
    return ipc_path
