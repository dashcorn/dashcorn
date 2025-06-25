import time
import threading
import logging

from prometheus_client import start_http_server, REGISTRY

from dashcorn.dashboard.prom_exporter import PrometheusExporter

logger = logging.getLogger(__name__)

class PrometheusHttpServer:
    def __init__(self, state_provider, prom_port=9100):
        """
        state_provider: Callable trả về RealtimeState dict
        prom_port: cổng exporter Prometheus
        """
        self.state_provider = state_provider
        self.prom_port = prom_port
        self._thread = None
        self._stop_event = threading.Event()
        self._running = False

    def start(self):
        if self._running:
            logger.debug(f"[{self.__class__.__name__}] already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_prometheus_exporter, daemon=True)
        self._thread.start()
        self._running = True

    def stop(self):
        if not self._running:
            logger.debug(f"[{self.__class__.__name__}] not running.")
            return

        self._stop_event.set()
        self._thread.join(timeout=5)
        self._running = False
        logger.debug(f"[{self.__class__.__name__}] stopped.")

    def restart(self):
        logger.debug(f"[{self.__class__.__name__}] restarting ...")
        self.stop()
        self.start()

    def _run_prometheus_exporter(self):
        try:
            exporter = PrometheusExporter(self.state_provider)
            REGISTRY.register(exporter)
            start_http_server(self.prom_port)
            logger.debug(f"[{self.__class__.__name__}] started on port {self.prom_port}.")
            while not self._stop_event.is_set():
                time.sleep(1)
        except Exception as e:
            logger.warning(f"[{self.__class__.__name__}] running error: {e}")
