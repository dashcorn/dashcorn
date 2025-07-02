import logging
import threading
import time
import zmq

from typing import Callable, Optional

from dashcorn.commons import consts
from dashcorn.utils.zmq_util import Protocol

logger = logging.getLogger(__name__)

class SettingsListener():
    def __init__(self, protocol: Protocol = "tcp",
            host=consts.ZMQ_CONNECTION_CONTROL_HOST,
            port=consts.ZMQ_CONNECTION_CONTROL_PORT,
            address: Optional[str] = None,
            endpoint: Optional[str] = None,
            handle_message: Optional[Callable]=None,
            socket_poll_enabled: bool = False,
            socket_poll_timeout:int|None=None,
            break_time:float=0.05):
        self._protocol = protocol
        self._address = address or f"{host}:{port}"
        self._endpoint = endpoint or f"{self._protocol}://{self._address}"
        self._handle_message = handle_message
        self._socket_poll_enabled = socket_poll_enabled
        self._socket_poll_timeout = socket_poll_timeout
        self._break_time = break_time
        self._context = None
        self._socket = None
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.debug(f"[{self.__class__.__name__}] Server already running.")
            return
        logger.debug(f"[{self.__class__.__name__}] Starting server thread...")

        self._stop_event.clear()
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.SUB)
        self._socket.connect(f"{self._endpoint}")
        self._socket.setsockopt_string(zmq.SUBSCRIBE, "")
        logger.debug(f"[{self.__class__.__name__}] Bound to {self._endpoint}")

        self._thread = threading.Thread(target=self._target, daemon=True)
        self._thread.start()
        logger.debug(f"[{self.__class__.__name__}] Server started.")

    def stop(self):
        logger.debug(f"[{self.__class__.__name__}] Stopping server thread...")
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        if self._socket:
            self._socket.close()
        if self._context:
            self._context.term()
        logger.debug(f"[{self.__class__.__name__}] Server stopped.")

    def restart(self):
        logger.debug(f"[{self.__class__.__name__}] Restarting server...")
        self.stop()
        self.start()

    def _target(self):
        while not self._stop_event.is_set():
            try:
                if self._socket_poll_enabled:
                    self._listen()
                else:
                    self._process()
            except zmq.ZMQError as e:
                if e.errno == zmq.ETERM:
                    logger.warning(f"[{self.__class__.__name__}] Context terminated.")
                elif e.errno == zmq.ENOTSOCK:
                    logger.warning(f"[{self.__class__.__name__}] Invalid socket.")
                else:
                    raise

    def _listen(self):
        if self._socket_poll(timeout=self._socket_poll_timeout):
            self._process()
        elif self._break_time > 0:
            time.sleep(self._break_time)

    def _socket_poll(self, timeout:int|None):
        return self._socket.poll(timeout=(100 if timeout is None else timeout), flags=zmq.POLLOUT)

    def _process(self):
        if self._handle_message and callable(self._handle_message):
            self._handle_message(self._socket.recv_json())
