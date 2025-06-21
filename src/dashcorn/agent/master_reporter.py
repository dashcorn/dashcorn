import os
import time
import threading
import logging
import socket
import psutil

from dashcorn.agent.zmq_client import send_metric

logger = logging.getLogger(__name__)

class DashcornAgentRunner:
    def __init__(self, interval: float = 5.0, log_sending_event: bool = True):
        self.interval = interval
        self.log_sending_event = log_sending_event
        self.running = False
        self.thread = None
        self.hostname = socket.gethostname()
        self.pid = os.getpid()

    def start(self):
        if self.running:
            return
        logger.info(f"🧠 Starting Dashcorn master agent in PID {self.pid}")
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        logger.info("🛑 Stopping Dashcorn master agent thread")

    def _loop(self):
        while self.running:
            try:
                self.report()
            except Exception as e:
                logger.exception(f"Error in Dashcorn master agent: {e}")
            time.sleep(self.interval)

    def report(self):
        process = psutil.Process(self.pid)

        info = {
            "type": "worker_status",
            "time": time.time(),
            "hostname": self.hostname,
            "master": {
                "pid": self.pid,
                "cpu": process.cpu_percent() / psutil.cpu_count(),
                "memory": process.memory_info().rss,
                "num_threads": process.num_threads(),
                "start_time": process.create_time(),
            },
            "workers": [],
        }

        for child in process.children(recursive=True):
            try:
                info["workers"].append({
                    "pid": child.pid,
                    "cpu": child.cpu_percent() / psutil.cpu_count(),
                    "memory": child.memory_info().rss,
                    "status": child.status(),
                    "start_time": child.create_time(),
                })
            except Exception:
                continue  # worker may have exited

        if self.log_sending_event:
            logger.debug(f"✅ send the worker_status[{self.hostname}] to the metrics collector")

        send_metric(info)
