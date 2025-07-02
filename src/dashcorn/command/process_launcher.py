from dashcorn.dashboard.process_executor import ProcessExecutor

import zmq
import json
import logging

from typing import Optional

logger = logging.getLogger(__name__)

class ProcessLauncher:
    def __init__(
        self,
        protocol: str = "ipc",
        address: str = "/tmp/dashcorn-pm.sock",
        endpoint: str = None,
    ):
        self._endpoint = endpoint or f"{protocol}://{address}"

        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REQ)
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
        result = self.send_command("start", {"name": name, "app_path": app_path, **kwargs})
        status = result.get("status")

        if status == "already_exists":
            print(f"[dashcorn] Process '{name}' already exists.")
            return result

        if status == "ok":
            pid = result.get("proc", {}).get("pid")
            print(f"[dashcorn] Starting process '{name}' started, pid: {pid}")
            return result

        return result

    def stop(self, name: str):
        result = self.send_command("stop", {"name": name})
        status = result.get("status")
        if status == "not_found":
            print(f"[dashcorn] Process '{name}' not found.")
            return result
        if status == "already_stopped":
            print(f"[dashcorn] Process '{name}' already stopped.")
            return result
        if status == "ok":
            pid = result.get("pid")
            print(f"[dashcorn] Stopped process '{name}' (PID: {pid})")
            return result
        return result

    def restart(self, name: str):
        result = self.send_command("restart", {"name": name})
        status = result.get("status")
        if status == "not_found":
            print(f"[dashcorn] Process '{name}' not found.")
            return result
        print(f"[dashcorn] Process '{name}' restarted.")
        return result

    def list(self):
        result = self.send_command("list")

        print(f"{'Name':<15}{'PID':<8}{'Status':<10}{'App Path'}")
        print("-" * 60)
        for meta in result.get("processes"):
            name = meta.get("name")
            pid = meta.get("pid")
            status = meta.get("status")
            app_path = meta.get("app_path")
            print(f"{name:<15}{pid:<8}{status:<10}{app_path}")

        return result

    def delete(self, name: str):
        result = self.send_command("delete", {"name": name})
        status = result.get("status")
        if status == "not_found":
            print(f"[dashcorn] Process '{name}' not found.")
        elif status == "ok":
            print(f"[dashcorn] Deleted process '{name}' from list.")
        return result
