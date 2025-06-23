import zmq
import threading
import logging
import json
import time

from dashcorn.dashboard.realtime_metrics import store

logger = logging.getLogger(__name__)

class MetricsCollector:
    """
    Listen for incoming metrics over a ZMQ PULL socket and update in-memory store.
    Designed to run in a background thread.
    """

    def __init__(self, bind_addr: str = "tcp://*:5556"):
        """
        Initialize the MetricsCollector.

        :param bind_addr: ZMQ bind address, typically 'tcp://*:5556'
        """
        self._bind_addr = bind_addr
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
            self._socket.bind(self._bind_addr)
            logger.debug(f"[{self.__class__.__name__}] Listening on {self._bind_addr}...")
        except zmq.ZMQError as e:
            logger.warning(f"[{self.__class__.__name__}] bind error: {e}")

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.debug(f"[{self.__class__.__name__}] started.")

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                raw = self._socket.recv()
                msg = json.loads(raw)
                self._handle_message(msg)
            except Exception as e:
                logger.warning(f"[{self.__class__.__name__}] Error while receiving or processing message: {e}")
                time.sleep(0.5)

    def _handle_message(self, msg: dict):
        msg_type = msg.get("type")
        if msg_type == "worker_status":
            store.update("server", msg)
        elif msg_type == "http":
            store.update("http", msg)
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
