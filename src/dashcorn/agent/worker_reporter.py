import threading
import time
import logging
from typing import Optional

from dashcorn.commons.agent_info_util import get_agent_id

from .proc_inspector import get_worker_metrics
from .settings_store import SettingsStore
from .worker_sender import MetricsSender

logger = logging.getLogger(__name__)

class WorkerReporter:
    """
    Periodically collects and sends worker-level metrics to the dashboard via ZMQ.

    This class runs a background thread to send data like CPU, memory usage,
    and thread count to the Dashcorn dashboard.

    Attributes:
        interval (float): Interval in seconds between metric reports.
        agent_id (str): Hostname used to identify this worker.
        sender (MetricsSender): The ZMQ sender used to push metrics.
    """

    def __init__(
        self,
        interval: float = 5.0,
        settings_store: Optional[SettingsStore] = None,
        metrics_sender: Optional[MetricsSender] = None,
        agent_id: Optional[str] = None,
        logging_enabled: bool = False,
    ):
        """
        Initialize the worker reporter.

        Args:
            interval (float): How often to send metrics (in seconds).
            metrics_sender (Optional[MetricsSender]): Optional external MetricsSender instance.
            agent_id (Optional[str]): Optional override of system agent_id.
        """
        self._interval = interval
        self._agent_id = agent_id or get_agent_id()
        self._settings_store = settings_store
        self._metrics_sender = metrics_sender
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._logging_enabled = logging_enabled

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                if self._metrics_sender:
                    metric = {
                        "type": "worker_status",
                        "agent_id": self._agent_id,
                        "timestamp": time.time(),
                        **get_worker_metrics(leader=self._settings_store.leader),
                    }
                    self._metrics_sender.send(metric)
                    if self._logging_enabled:
                        logger.debug(f"[{self.__class__.__name__}] Sent worker metrics: {metric}")
                else:
                    logger.warning(f"[{self.__class__.__name__}] metrics_sender is None")
            except Exception as e:
                logger.warning(f"[{self.__class__.__name__}] Failed to send metrics: {e}")
            self._stop_event.wait(self._interval)

    def start(self):
        """
        Start the background reporting thread.
        """
        if self._thread and self._thread.is_alive():
            return  # Already running
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        if self._logging_enabled:
            logger.debug(f"[{self.__class__.__name__}] Reporter thread started.")

    def stop(self):
        """
        Stop the background reporting thread.
        """
        if not self._thread or not self._thread.is_alive():
            return
        self._stop_event.set()
        self._thread.join(timeout=self._interval + 1)
        if self._logging_enabled:
            logger.debug(f"[{self.__class__.__name__}] Reporter thread stopped.")

    def restart(self):
        """
        Restart the background reporting thread.
        """
        self.stop()
        self.start()
