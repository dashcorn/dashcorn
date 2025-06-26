import time
import threading
import logging

class PromMetricsScheduler:
    def __init__(self, exporter, interval=4.0):
        self.exporter = exporter
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread = None

    def _loop(self):
        while not self._stop_event.is_set():
            self.exporter.aggregate_http_events()
            time.sleep(self.interval)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()
