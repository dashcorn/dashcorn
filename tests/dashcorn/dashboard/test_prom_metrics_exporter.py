import pytest
import time

from dashcorn.dashboard.prom_metrics_exporter import PromMetricsExporter

class DummyState:
    def __init__(self):
        self._http_events = [
            {
                "agent_id": "agent-A",
                "method": "GET",
                "path": "/test",
                "status": 200,
                "duration": 0.123,
                "time": time.time(),
                "pid": 1234,
            },
            {
                "agent_id": "agent-A",
                "method": "GET",
                "path": "/test",
                "status": 200,
                "duration": 0.234,
                "time": time.time() - 5,  # Not in progress
                "pid": 1234,
            },
        ]

        self._servers = {
            "agent-A": {
                "master": {
                    "pid": 1,
                    "start_time": time.time() - 500,
                },
                "workers": {
                    "1234": {
                        "cpu": 3.5,
                        "memory": 1024 * 1024 * 50,
                        "num_threads": 7,
                        "start_time": time.time() - 100,
                    },
                    "5678": {
                        "cpu": 4.0,
                        "memory": 1024 * 1024 * 60,
                        "num_threads": 5,
                        "start_time": time.time() - 50,
                    },
                }
            }
        }

    def get_http_events(self, cleancut=True):
        return self._http_events

    def get_all_servers(self):
        return self._servers

def test_prom_metrics_exporter_collect():
    state = DummyState()
    exporter = PromMetricsExporter(state_provider=lambda: state)

    exporter.aggregate_http_events()
    collected = list(exporter.collect())

    # Helper to find metric by name
    def get_metric(name):
        for m in collected:
            if m.name == name:
                return m
        return None

    req_total = get_metric("uvicorn_requests")
    assert req_total is not None
    assert any(s.labels == {'agent_id': 'agent-A', 'method': 'GET', 'path': '/test', 'status': '200'} and 
        s.value == 2 for s in req_total.samples)

    req_in_progress = get_metric("uvicorn_requests_in_progress")
    assert req_in_progress is not None
    # Only 1 is within 4s
    assert any(s.labels == {'agent_id': 'agent-A', 'method': 'GET', 'path': '/test'} and
        s.value == 1 for s in req_in_progress.samples)

    req_duration = get_metric("uvicorn_requests_duration_seconds")
    assert req_duration is not None
    duration_sum_samples = [
        s.value for s in req_duration.samples
        if s.name == "uvicorn_requests_duration_seconds_sum"
    ]
    total_dur = sum(duration_sum_samples)
    assert total_dur == pytest.approx(0.123 + 0.234, rel=1e-2)

    cpu_total = get_metric("uvicorn_total_cpu_percent")
    assert cpu_total is not None
    assert any(s.labels == {'agent_id': 'agent-A'} and s.value == pytest.approx(3.5 + 4.0, rel=1e-2) for s in cpu_total.samples)

    mem_total = get_metric("uvicorn_total_memory_bytes")
    assert mem_total is not None
    assert any(s.labels == {'agent_id': 'agent-A'} and s.value > 0 for s in mem_total.samples)

    active_worker = get_metric("uvicorn_active_worker_count")
    assert active_worker is not None
    assert any(s.labels == {'agent_id': 'agent-A'} and s.value == 2 for s in active_worker.samples)

    master_uptime = get_metric("uvicorn_master_uptime_seconds")
    assert master_uptime is not None
    assert any(s.labels == {'agent_id': 'agent-A', 'pid': '1'} and s.value > 400 for s in master_uptime.samples)


def test_prom_exporter_with_prefix():
    # Giả lập state
    def fake_state():
        return type("FakeState", (), {
            "get_http_events": lambda self, cleancut=False: [
                {
                    "agent_id": "agentX",
                    "method": "POST",
                    "path": "/v1/test",
                    "status": 201,
                    "duration": 0.456,
                    "time": time.time(),
                    "pid": 1234
                }
            ],
            "get_all_servers": lambda self: {
                "agentX": {
                    "workers": {
                        "1234": {
                            "cpu": 12.0,
                            "memory": 6543210,
                            "num_threads": 5,
                            "start_time": time.time() - 20,
                            "pid": 1234
                        }
                    },
                    "master": {
                        "pid": 1,
                        "start_time": time.time() - 100
                    }
                }
            }
        })()

    exporter = PromMetricsExporter(state_provider=fake_state, metric_label_prefix="demo")
    exporter.aggregate_http_events()
    collected = list(exporter.collect())

    # Kiểm tra tên các metric đều có prefix
    for metric in collected:
        assert metric.name.startswith("demo_")

    # Kiểm tra histogram chứa sample đúng
    duration_histogram = next((m for m in collected if m.name == "demo_requests_duration_seconds"), None)
    assert duration_histogram is not None

    sum_sample = next((s for s in duration_histogram.samples if s.name == "demo_requests_duration_seconds_sum"), None)
    count_sample = next((s for s in duration_histogram.samples if s.name == "demo_requests_duration_seconds_count"), None)

    assert sum_sample is not None
    assert count_sample is not None
    assert sum_sample.value == pytest.approx(0.456, rel=1e-2)
    assert count_sample.value == 1
