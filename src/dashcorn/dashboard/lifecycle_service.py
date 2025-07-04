import os
import signal
import time
import threading
import logging

from pathlib import Path
from typing import Callable, List

logger = logging.Logger(__name__)

PID_FILE = Path.home() / ".config" / "dashcorn" / "hub.pid"
PID_FILE.parent.mkdir(parents=True, exist_ok=True)

class LifecycleService:
    def __init__(
        self,
        on_startup: List[Callable[[], None]] = None,
        on_shutdown: List[Callable[[], None]] = None,
    ):
        self.on_startup = on_startup or []
        self.on_shutdown = on_shutdown or []
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.debug(f"[{self.__class__.__name__}] Server already running.")
            return

        if self._is_already_running():
            logger.warning(f"[{self.__class__.__name__}] Server already running. Aborting startup.")
            return

        self._write_pid_file()

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

        self._remove_pid_file()
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

    def _write_pid_file(self):
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        logger.debug(f"PID written to {PID_FILE}")

    def _remove_pid_file(self):
        try:
            PID_FILE.unlink()
            logger.debug(f"PID file {PID_FILE} removed.")
        except FileNotFoundError:
            pass

    def _is_already_running(self) -> bool:
        if not PID_FILE.exists():
            return False
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # Gửi tín hiệu 0 để kiểm tra tồn tại
        except (ValueError, ProcessLookupError, PermissionError, OSError):
            return False
        return True
