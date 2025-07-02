import zmq
import threading
import logging
import time

from typing import Optional

from dashcorn.commons import consts
from dashcorn.dashboard.realtime_metrics import RealtimeState
from dashcorn.utils.zmq_util import Protocol, renew_zmq_ipc_socket

logger = logging.getLogger(__name__)

class MetricsCollector:
    """
    Listen for incoming metrics over a ZMQ PULL socket and update in-memory store.
    Designed to run in a background thread.
    """

    def __init__(self,
            protocol: Protocol = "tcp",
            address: Optional[str] = f"*:{consts.ZMQ_CONNECTION_METRICS_PORT}",
            endpoint: Optional[str] = None,
            state_store: Optional[RealtimeState] = None):
        """
        Initialize the MetricsCollector.

        :param endpoint: ZMQ bind address, typically 'tcp://*:5555'
        """
        self._protocol = protocol
        self._address = renew_zmq_ipc_socket(address, protocol)
        self._endpoint = endpoint or f"{self._protocol}://{self._address}"
        self._state_store = state_store
        self._context = None
        self._socket = None
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        """Start the listener in a background thread."""
        if self._thread and self._thread.is_alive():
            logger.debug(f"[{self.__class__.__name__}] is already running.")
            return

        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.PULL)
        try:
            self._socket.bind(self._endpoint)
            logger.debug(f"[{self.__class__.__name__}] Listening on {self._endpoint}...")
        except zmq.ZMQError as e:
            logger.warning(f"[{self.__class__.__name__}] bind error: {e}")
            raise e

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.debug(f"[{self.__class__.__name__}] started.")

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                self._handle_message(self._socket.recv_json())
            except Exception as e:
                logger.warning(f"[{self.__class__.__name__}] Error while receiving or processing message: {e}")
                time.sleep(0.5)

    def _handle_message(self, msg: dict):
        msg_type = msg.get("type")
        if msg_type == "worker_status":
            if self._state_store:
                self._state_store.update("server", msg)
        elif msg_type == "http":
            if self._state_store:
                self._state_store.update("http", msg)
        else:
            logger.warning(f"[{self.__class__.__name__}] Unknown message type: {msg_type}")

    def stop(self):
        """Stop the listener."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        if self._socket:
            self._socket.close(linger=0)
        if self._context:
            self._context.term()
        logger.debug(f"[{self.__class__.__name__}] stopped.")

    def restart(self):
        """Restart the listener."""
        self.stop()
        time.sleep(0.5)
        self.start()
