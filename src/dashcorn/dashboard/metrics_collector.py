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
        self._context = zmq.Context.instance()
        self._socket = self._context.socket(zmq.PULL)
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        """Start the listener in a background thread."""
        if self._thread and self._thread.is_alive():
            logger.debug("MetricsCollector is already running.")
            return

        self._context = zmq.Context.instance()
        self._socket = self._context.socket(zmq.PULL)
        try:
            self._socket.bind(self._bind_addr)
            logger.debug(f"[ZMQ] Listening on {self._bind_addr}...")
        except zmq.ZMQError as e:
            logger.debug(f"ZMQ bind error: {e}")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.debug("MetricsCollector started.")

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                if self._socket.poll(100):  # wait max 100ms
                    raw = self._socket.recv()
                    msg = json.loads(raw)
                    self._handle_message(msg)
            except Exception as e:
                logger.warning(f"[ZMQ] Error while receiving or processing message: {e}")
                time.sleep(0.5)

    def _handle_message(self, msg: dict):
        msg_type = msg.get("type")
        if msg_type == "worker_status":
            store.update("server", msg)
            # db.save_worker_info(msg)
        elif msg_type == "http":
            store.update("http", msg)
            # db.save_http_metric(msg)
        else:
            logger.warning(f"[ZMQ] Unknown message type: {msg_type}")

    def stop(self):
        """Stop the listener."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        if self._socket:
            self._socket.close(linger=0)
        if self._context:
            self._context.term()
        logger.info("MetricsCollector stopped.")

    def restart(self):
        """Restart the listener."""
        self.stop()
        time.sleep(0.5)
        self.start()
