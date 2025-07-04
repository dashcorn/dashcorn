import os
import signal
import time
import threading
import logging

from pathlib import Path
from typing import Callable, List

logger = logging.Logger(__name__)

class classproperty(property):
    def __get__(self, obj, objtype=None):
        return self.fget(objtype)

class LifecycleService:
    def __init__(
        self,
        on_startup: List[Callable[[], None]] = None,
        on_shutdown: List[Callable[[], None]] = None,
        self_managed: bool = False,
    ):
        self.on_startup = on_startup or []
        self.on_shutdown = on_shutdown or []
        self._self_managed = self_managed
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.debug(f"[{self.__class__.__name__}] Server already running.")
            return

        if self._self_managed:
            if self.is_pid_alive():
                logger.warning(f"[{self.__class__.__name__}] Server already running. Aborting startup.")
                return

            self.write_pid_file()

        logger.debug(f"[{self.__class__.__name__}] Starting server ...")

        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        for func in self.on_startup:
            logger.debug(f"[{self.__class__.__name__}] 🚀 Running startup hook: {func.__name__}")
            func()

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._target, daemon=False)
        self._thread.start()
        logger.debug(f"[{self.__class__.__name__}] Server started.")

    def _handle_signal(self, signum, frame):
        logger.debug(f"[{self.__class__.__name__}] Caught signal {signum}, initiating shutdown...")
        self.stop()

    def stop(self):
        logger.debug(f"[{self.__class__.__name__}] Gracefully shutting down...")
        self._stop_event.set()

        for func in self.on_shutdown:
            logger.debug(f"[{self.__class__.__name__}] 🧹 Running shutdown hook: {func.__name__}")
            func()

        if self._thread:
            self._thread.join(timeout=5)

        if self._self_managed:
            self.remove_pid_file()

        logger.debug(f"[{self.__class__.__name__}] Server stopped.")

    def restart(self):
        logger.debug(f"[{self.__class__.__name__}] Restarting server...")
        self.stop()
        self.start()

    def _target(self):
        while not self._stop_event.is_set():
            self._process()

    def _process(self):
        print(f"[{self.__class__.__name__}] heartbeat ...")
        time.sleep(2)

    _pid_file = None

    @classproperty
    def pid_file(cls):
        if cls._pid_file is None:
            cls._pid_file = Path.home() / ".config" / "dashcorn" / "hub.pid"
            cls._pid_file.parent.mkdir(parents=True, exist_ok=True)
        return cls._pid_file

    @classmethod
    def read_pid_file(cls):
        try:
            return int(cls.pid_file.read_text())
        except Exception:
            return 0

    @classmethod
    def write_pid_file(self):
        with open(self.pid_file, "w") as f:
            f.write(str(os.getpid()))
        logger.debug(f"PID written to {self.pid_file}")

    @classmethod
    def remove_pid_file(self):
        try:
            self.pid_file.unlink()
            logger.debug(f"PID file {self.pid_file} removed.")
        except FileNotFoundError:
            pass

    @classmethod
    def is_pid_alive(self) -> bool:
        if not self.pid_file.exists():
            return False
        try:
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # Gửi tín hiệu 0 để kiểm tra tồn tại
        except (ValueError, ProcessLookupError, PermissionError, OSError):
            return False
        return True
