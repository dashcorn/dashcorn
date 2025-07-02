from dashcorn.dashboard.process_executor import ProcessExecutor

import os
import logging
import zmq

from typing import Optional

DEFAULT_SOCKET_PATH = "/tmp/dashcorn-pm.sock"
DEFAULT_TIMEOUT_MS = int(os.getenv("DASHCORN_ZMQ_TIMEOUT_MS", "5000"))

logger = logging.getLogger(__name__)

class ProcessLauncher:
    def __init__(
        self,
        protocol: str = "ipc",
        address: str = DEFAULT_SOCKET_PATH,
        endpoint: str = None,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
    ):
        self._endpoint = endpoint or f"{protocol}://{address}"
        self._timeout_ms = timeout_ms

        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REQ)
        self._socket.RCVTIMEO = self._timeout_ms
        self._socket.LINGER = 0  # avoid long waits when closing
        self._socket.connect(self._endpoint)

    def send_command(self, cmd: str, args: Optional[dict] = None) -> dict:
        payload = {"cmd": cmd, "args": args or {}}
        try:
            self._socket.send_json(payload)
            reply = self._socket.recv_json()
            return reply
        except Exception as e:
            logger.exception(f"[dashcorn] Failed to send command: {cmd}")
            return {"status": "error", "message": str(e)}

    def start(self, name: str, app_path: str, **kwargs):
        return self.send_command("start", {"name": name, "app_path": app_path, **kwargs})

    def stop(self, name: str):
        return self.send_command("stop", {"name": name})

    def restart(self, name: str):
        return self.send_command("restart", {"name": name})

    def list(self):
        return self.send_command("list")

    def delete(self, name: str):
        return self.send_command("delete", {"name": name})
