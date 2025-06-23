import threading
import time
import logging
from typing import Optional

from dashcorn.dashboard.realtime_metrics import store
from dashcorn.dashboard.settings_publisher import SettingsPublisher

logger = logging.getLogger(__name__)


class SettingsSelector:
    """
    Run a background thread to periodically elect a leader worker
    and broadcast it via SettingsPublisher.
    """

    def __init__(self, interval: float = 5.0,
            settings_publisher:Optional[SettingsPublisher] = None):
        """
        :param interval: Time (in seconds) between leader elections.
        """
        self._interval = interval
        self._publisher = settings_publisher
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def _run_loop(self):
        logger.debug(f"[{self.__class__.__name__}] loop started.")
        while not self._stop_event.is_set():
            try:
                for control_packet in store.elect_leaders():
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
        if not self._thread or not self._thread.is_alive():
            logger.debug(f"[{self.__class__.__name__}] stopped.")
            return
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        logger.debug(f"[{self.__class__.__name__}] stopped.")

    def restart(self):
        """Restart the leader election process."""
        self.stop()
        self.start()
