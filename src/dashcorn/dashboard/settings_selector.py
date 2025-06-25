import threading
import time
import logging
from typing import Optional

from dashcorn.dashboard.realtime_metrics import RealtimeState
from dashcorn.dashboard.settings_publisher import SettingsPublisher

logger = logging.getLogger(__name__)


class SettingsSelector:
    """
    Run a background thread to periodically elect a leader worker
    and broadcast it via SettingsPublisher.
    """

    def __init__(self, interval: float = 5.0,
            settings_publisher: Optional[SettingsPublisher] = None,
            state_store: Optional[RealtimeState] = None):
        """
        :param interval: Time (in seconds) between leader elections.
        """
        self._interval = interval
        self._publisher = settings_publisher
        self._state_store = state_store
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def _run_loop(self):
        if self._state_store is None:
            logger.warning(f"[{self.__class__.__name__}] 'state_store' is None, loop is stopped")
        logger.debug(f"[{self.__class__.__name__}] loop is running...")
        while not self._stop_event.is_set():
            try:
                for control_packet in self._state_store.elect_leaders():
                    self._publisher.publish(control_packet)
                    logger.debug(f"[{self.__class__.__name__}] Published new packet: {control_packet}")
            except Exception as e:
                logger.warning(f"[{self.__class__.__name__}] Leader election failed: {e}")
            time.sleep(self._interval)

    def start(self):
        """Start the background leader election thread."""
        if self._thread and self._thread.is_alive():
            logger.debug(f"[{self.__class__.__name__}] is already running.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.debug(f"[{self.__class__.__name__}] started.")

    def stop(self):
        """Stop the leader election thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        logger.debug(f"[{self.__class__.__name__}] stopped.")

    def restart(self):
        """Restart the leader election process."""
        self.stop()
        self.start()
