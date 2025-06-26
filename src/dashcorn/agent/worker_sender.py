import zmq
import logging

from typing import Optional

from dashcorn.utils.zmq_util import Protocol

logger = logging.getLogger(__name__)

class MetricsSender:
    """
    A lightweight ZMQ PUSH sender for delivering metrics to the Dashcorn dashboard.

    This class is used by agents running inside Uvicorn workers to push structured
    JSON metrics to the central dashboard. It uses the ZeroMQ PUSH socket pattern,
    designed to be fire-and-forget with minimal overhead.

    Attributes:
        host (str): The hostname of the dashboard (default "127.0.0.1").
        port (int): The port of the dashboard's ZMQ PULL socket (default 5556).
        context (zmq.Context): The ZMQ context used to create the socket.
        logging_enabled (bool): Whether debug logging is enabled.
    """

    def __init__(
        self,
        protocol: Protocol = "tcp",
        host: str = "127.0.0.1",
        port: int = 5556,
        address: Optional[str] = None,
        endpoint: Optional[str] = None,
        context: Optional[zmq.Context] = None,
        logging_enabled: bool = False,
    ):
        """
        Initialize the MetricsSender.

        Args:
            host (str): The IP address or hostname of the dashboard server.
            port (int): The port number where the dashboard's ZMQ PULL socket is bound.
            context (Optional[zmq.Context]): An optional shared ZMQ context. If None,
                                             a new instance or singleton is used.
            logging_enabled (bool): If True, enable debug logging of connection and sending.
        """
        self._protocol = protocol
        self._host = host
        self._port = port
        self._address = address or f"{self._host}:{self._port}"
        self._endpoint = endpoint or f"{self._protocol}://{self._address}"
        self._is_shared_context = context is not None
        self._context = context or zmq.Context()
        self._socket = self._context.socket(zmq.PUSH)
        self._logging_enabled = logging_enabled

        try:
            self._socket.connect(self._endpoint)
            if self._logging_enabled:
                logger.debug(f"[{self.__class__.__name__}] connected to dashboard at {self._endpoint}")
        except Exception as e:
            logger.warning(f"[{self.__class__.__name__}] failed to connect to dashboard at {self._endpoint}: {e}")

    def send(self, data: dict):
        """
        Send a metric payload to the dashboard.

        The payload should be a serializable dictionary. This method will attempt
        to encode it as JSON and send it over the ZMQ PUSH socket.

        Args:
            data (dict): The dictionary containing metric data to send.
        """
        try:
            self._socket.send_json(data)
            if self._logging_enabled:
                logger.debug(f"[{self.__class__.__name__}] sent metric: {data}")
        except Exception as e:
            logger.warning(f"[{self.__class__.__name__}] failed to send metric via ZMQ: {e}")

    def close(self):
        """
        Close the underlying ZMQ socket and context.

        This method should be called when the sender is no longer needed
        to ensure proper cleanup of ZMQ resources.
        """
        try:
            self._socket.close()
            if not self._is_shared_context:
                self._context.term()
            if self._logging_enabled:
                logger.debug(f"[{self.__class__.__name__}] socket closed.")
        except Exception as e:
            logger.warning(f"[{self.__class__.__name__}] error closing socket: {e}")
