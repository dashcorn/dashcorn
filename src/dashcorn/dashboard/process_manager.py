import zmq
import threading
import time
import logging

from typing import Optional
from .process_executor import ProcessExecutor
from dashcorn.utils.zmq_util import Protocol, renew_zmq_ipc_socket

logger = logging.getLogger(__name__)

class ProcessManager:
    def __init__(self,
            protocol: Protocol = "ipc",
            address: str = "/tmp/dashcorn-pm.sock",
            endpoint: str = None,
            process_executor: Optional[ProcessExecutor] = None,
    ):
        self.protocol = protocol
        self.address = renew_zmq_ipc_socket(address, protocol)
        self.endpoint = endpoint or f"{protocol}://{address}"

        self._process_executor = process_executor or ProcessExecutor()

        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.debug("ProcessManager is already running.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.debug(f"ProcessManager started at {self.endpoint}")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        logger.debug("ProcessManager stopped.")

    def restart(self):
        self.stop()
        time.sleep(0.2)
        self.start()

    def _run(self):
        ctx = zmq.Context()
        socket = ctx.socket(zmq.REP)
        socket.bind(self.endpoint)
        logger.debug(f"ZMQ REP socket bound to {self.endpoint}")

        while not self._stop_event.is_set():
            try:
                if socket.poll(100):  # wait for 100ms
                    socket.send_json(self.process(socket.recv_json()))
            except zmq.ZMQError as e:
                if self._stop_event.is_set():
                    break  # graceful exit
                logger.warning("ZMQ error in ProcessManager loop.")
            except Exception as ex:
                logger.warning("Unexpected error in ProcessManager loop.")
                try:
                    socket.send_json({"status": "error", "message": str(ex)})
                except Exception:
                    pass

        socket.close()
        ctx.term()

    def process(self, request: dict) -> dict:
        logger.debug(f"Received request: {request}")
        cmd = request.get("cmd")
        args = request.get("args", {})
        handler = getattr(self._process_executor, cmd, None)
        if not callable(handler):
            return {"status": "error", "message": f"Unknown command: {cmd}"}
        return handler(**args)
