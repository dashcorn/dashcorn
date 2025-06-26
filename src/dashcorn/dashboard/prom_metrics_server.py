import time
import threading
import logging

from prometheus_client import REGISTRY, make_wsgi_app
from wsgiref.simple_server import make_server

logger = logging.getLogger(__name__)

class PromMetricsServer:
    def __init__(self, exporter, prom_port=9100, prom_host=''):
        """
        state_provider: Callable trả về RealtimeState dict
        prom_port: cổng exporter Prometheus
        """
        self._exporter = exporter
        self._prom_host = prom_host
        self._prom_port = prom_port
        self._server = None
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
        logger.debug(f"[{self.__class__.__name__}] started on port {self._prom_port}.")

    def stop(self):
        if not self._running:
            logger.debug(f"[{self.__class__.__name__}] not running.")
            return

        self._stop_event.set()
        if self._server:
            self._server.shutdown()
        self._thread.join(timeout=5)
        self._running = False
        logger.debug(f"[{self.__class__.__name__}] stopped.")

    def restart(self):
        logger.debug(f"[{self.__class__.__name__}] restarting ...")
        self.stop()
        self.start()

    def _run_prometheus_exporter(self):
        try:
            REGISTRY.register(self._exporter)
            app = make_wsgi_app(registry=REGISTRY)
            self._server = make_server(self._prom_host, self._prom_port, app)
            self._server.serve_forever()
        except Exception as e:
            logger.warning(f"[{self.__class__.__name__}] running error: {e}")
