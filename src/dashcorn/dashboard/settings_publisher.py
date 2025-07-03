import zmq
import time
import logging
from typing import Optional

from dashcorn.commons import consts
from dashcorn.utils.zmq_util import Protocol, renew_zmq_ipc_socket

logger = logging.getLogger(__name__)

class SettingsPublisher:
    """
    Publish system-wide settings (e.g. current leader PID) over a ZMQ PUB socket.
    """

    def __init__(self, protocol: Protocol = "tcp",
            host: str = consts.ZMQ_CONNECTION_CONTROL_HOST,
            port: int = consts.ZMQ_CONNECTION_CONTROL_PORT,
            address: Optional[str] = None,
            endpoint: Optional[str] = None,
            context: Optional[zmq.Context] = None,
            delay_before_send: float = 1.0,
            publish_log_enabled: bool = False):
        """
        Initialize the ZMQ PUB publisher.

        :param host: Host to bind the PUB socket on.
        :param port: Port to bind the PUB socket on.
        :param context: Optional shared ZMQ context.
        :param delay_before_send: Optional delay before first send to allow subscriber to connect.
        """
        self._protocol = protocol
        self._address = renew_zmq_ipc_socket(address, self._protocol) or f"{host}:{port}"
        self._endpoint = endpoint or f"{self._protocol}://{self._address}"
        self._is_shared_context = context is not None
        self._context = context or zmq.Context.instance()
        self._socket = self._context.socket(zmq.PUB)
        self._delay = delay_before_send
        self._publish_log_enabled = publish_log_enabled

    def open(self):
        try:
            self._socket.bind(self._endpoint)
            logger.debug(f"[{self.__class__.__name__}] bound to {self._endpoint}")
        except Exception as e:
            logger.warning(f"[{self.__class__.__name__}] Failed to bind PUB socket on {self._endpoint}: {e}")

    def publish(self, data: dict):
        """
        Send a JSON-serializable dictionary to all subscribers.

        :param data: Dictionary data to send.
        """
        try:
            time.sleep(self._delay)  # Ensure subscribers have time to connect
            self._socket.send_json(data)
            if self._publish_log_enabled:
                logger.debug(f"[{self.__class__.__name__}] Message: {data} published")
        except Exception as e:
            logger.warning(f"[{self.__class__.__name__}] Error publishing data via ZMQ: {e}")

    def close(self):
        """Cleanly close the PUB socket."""
        try:
            self._socket.close()
            logger.debug(f"[{self.__class__.__name__}] socket closed.")
            if not self._is_shared_context:
                self._context.term()
                logger.debug(f"[{self.__class__.__name__}] context terminated.")
        except Exception as e:
            logger.warning(f"[{self.__class__.__name__}] Error closing PUB socket: {e}")
