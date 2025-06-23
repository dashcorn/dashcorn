import zmq
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SettingsPublisher:
    """
    Publish system-wide settings (e.g. current leader PID) over a ZMQ PUB socket.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5557,
            context: Optional[zmq.Context] = None,
            delay_before_send: float = 1.0):
        """
        Initialize the ZMQ PUB publisher.

        :param host: Host to bind the PUB socket on.
        :param port: Port to bind the PUB socket on.
        :param context: Optional shared ZMQ context.
        :param delay_before_send: Optional delay before first send to allow subscriber to connect.
        """
        self._endpoint = f"tcp://{host}:{port}"
        self._is_shared_context = context is not None
        self._context = context or zmq.Context.instance()
        self._socket = self._context.socket(zmq.PUB)
        self._delay = delay_before_send

        try:
            self._socket.bind(self._endpoint)
            logger.debug(f"SettingsPublisher bound to {self._endpoint}")
        except Exception as e:
            logger.warning(f"Failed to bind PUB socket on {self._endpoint}: {e}")

    def publish(self, data: dict):
        """
        Send a JSON-serializable dictionary to all subscribers.

        :param data: Dictionary data to send.
        """
        try:
            time.sleep(self._delay)  # Ensure subscribers have time to connect
            self._socket.send_json(data)
            logger.debug(f"Published data: {data}")
        except Exception as e:
            logger.warning(f"Error publishing data via ZMQ: {e}")

    def close(self):
        """Cleanly close the PUB socket."""
        try:
            self._socket.close()
            if not self._is_shared_context:
                self._context.term()
            logger.debug("SettingsPublisher socket closed.")
        except Exception as e:
            logger.warning(f"Error closing PUB socket: {e}")
