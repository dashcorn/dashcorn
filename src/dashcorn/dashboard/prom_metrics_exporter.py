import time
import threading
import logging

from collections import defaultdict
from prometheus_client.core import (
    GaugeMetricFamily,
    CounterMetricFamily,
    HistogramMetricFamily,
)

logger = logging.getLogger(__name__)

class PromMetricsExporter:
    def __init__(self, state_provider, enable_logging: bool = False):
        """
        state_provider: Callable không đối số, trả về dict RealtimeState.
        Cấu trúc gồm:
            - 'http': list các requests
            - 'server': dict agent_id -> {master, workers}
        """
        self._state_provider = state_provider
        self._enable_logging = enable_logging

        self._accum_total = defaultdict(int)
        self._accum_by_worker = defaultdict(int)
        self._accum_duration_sum = defaultdict(float)
        self._accum_duration_count = defaultdict(int)
        self._accum_in_progress = defaultdict(int)
        self._lock = threading.Lock()

    def aggregate_http_events(self):
        state = self._state_provider()
        now = time.time()

        with self._lock:
            self._accum_in_progress = defaultdict(int)

        for req in state.get_http_events(cleancut=True):
            agent_id = req.get("agent_id", None)
            if agent_id is None:
                logger.warning(f"'agent_id' not found in http_event: {req}")
                continue

            method = req["method"]
            path = req["path"]
            status = str(req["status"])
            duration = req["duration"]
            pid = str(req["pid"])

            with self._lock:
                self._accum_total[(agent_id, method, path, status)] += 1
                self._accum_by_worker[(agent_id, pid)] += 1
                self._accum_duration_sum[(agent_id, method, path)] += duration
                self._accum_duration_count[(agent_id, method, path)] += 1
                if now - req["time"] < 4:
                    self._accum_in_progress[(agent_id, method, path)] += 1

    def collect(self):
        # ============ Request metrics ============
        req_total = CounterMetricFamily(
            "uvicorn_requests_total",
            "Total number of HTTP requests",
            labels=["agent_id", "method", "path", "status"],
        )
        req_by_worker = CounterMetricFamily(
            "uvicorn_requests_by_worker_total",
            "Total HTTP requests per worker",
            labels=["agent_id", "pid"],
        )
        req_duration = HistogramMetricFamily(
            "uvicorn_requests_duration_seconds",
            "Request duration (seconds)",
            labels=["agent_id", "method", "path"],
        )
        req_in_progress = GaugeMetricFamily(
            "uvicorn_requests_in_progress",
            "Number of in-progress HTTP requests",
            labels=["agent_id", "method", "path"],
        )

        for (agent_id, method, path, status), value in self._accum_total.items():
            req_total.add_metric([agent_id, method, path, status], value)

        for (agent_id, pid), value in self._accum_by_worker.items():
            req_by_worker.add_metric([agent_id, pid], value)

        for (agent_id, method, path), count in self._accum_duration_count.items():
            req_duration.add_sample(
                "uvicorn_requests_duration_seconds_sum",
                value=self._accum_duration_sum[(agent_id, method, path)],
                labels={"agent_id": agent_id, "method": method, "path": path},
            )
            req_duration.add_sample(
                "uvicorn_requests_duration_seconds_count",
                value=count,
                labels={"agent_id": agent_id, "method": method, "path": path},
            )

        for (agent_id, method, path), value in self._accum_in_progress.items():
            req_in_progress.add_metric([agent_id, method, path], value)

        yield req_total
        yield req_duration
        yield req_in_progress
        yield req_by_worker

        # ============ Worker + Master metrics ============
        cpu_total = defaultdict(float)
        mem_total = defaultdict(float)
        worker_count = defaultdict(int)

        state = self._state_provider()

        for agent_id, info in state.get_all_servers().items():
            workers = info.get("workers", {})
            master = info.get("master", {})

            for pid_str, w in workers.items():
                labels = [agent_id, pid_str]

                g = GaugeMetricFamily(
                    "uvicorn_worker_cpu_percent",
                    "CPU usage (%) per worker",
                    labels=["agent_id", "pid"]
                )
                g.add_metric(labels, w.get("cpu", 0.0))
                yield g

                g2 =GaugeMetricFamily(
                    "uvicorn_worker_memory_bytes",
                    "Memory usage in bytes",
                    labels=["agent_id", "pid"]
                )
                g2.add_metric(labels, w.get("memory", 0.0))
                yield g2

                g3 = GaugeMetricFamily(
                    "uvicorn_worker_thread_count",
                    "Thread count per worker",
                    labels=["agent_id", "pid"]
                )
                g3.add_metric(labels, w.get("num_threads", 0))
                yield g3

                now = time.time()
                uptime = max(0, now - w.get("start_time", now))
                g4 = GaugeMetricFamily(
                    "uvicorn_worker_uptime_seconds",
                    "Worker uptime in seconds",
                    labels=["agent_id", "pid"]
                )
                g4.add_metric(labels, uptime)
                yield g4

                cpu_total[agent_id] += w.get("cpu", 0.0)
                mem_total[agent_id] += w.get("memory", 0.0)
                worker_count[agent_id] += 1

            if "start_time" in master:
                pid = str(master.get("pid", "master"))
                uptime = max(0, now - master["start_time"])
                g5 = GaugeMetricFamily(
                    "uvicorn_master_uptime_seconds",
                    "Uptime of master process",
                    labels=["agent_id", "pid"]
                )
                g5.add_metric([agent_id, pid], uptime)
                yield g5

        for agent_id in cpu_total:
            g6 = GaugeMetricFamily(
                "uvicorn_total_cpu_percent",
                "Total CPU usage (%) per agent",
                labels=["agent_id"])
            g6.add_metric([agent_id], cpu_total[agent_id])
            yield g6

            g7 = GaugeMetricFamily(
                "uvicorn_total_memory_bytes",
                "Total memory usage (bytes) per agent",
                labels=["agent_id"])
            g7.add_metric([agent_id], mem_total[agent_id])
            yield g7

            g8 = GaugeMetricFamily(
                "uvicorn_active_worker_count",
                "Number of active workers",
                labels=["agent_id"])
            g8.add_metric([agent_id], worker_count[agent_id])
            yield g8
