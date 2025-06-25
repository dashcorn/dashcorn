from fastapi import FastAPI

from dashcorn.dashboard.config import DashboardConfig
from dashcorn.dashboard.realtime_metrics import RealtimeState
from dashcorn.dashboard.settings_selector import SettingsSelector
from dashcorn.dashboard.settings_publisher import SettingsPublisher
from dashcorn.dashboard.metrics_collector import MetricsCollector
from dashcorn.dashboard.prom_http_server import PrometheusHttpServer

import dashcorn.utils.logging

config = DashboardConfig()

store = RealtimeState()

settings_publisher = SettingsPublisher(
    protocol=config.zmq_pub_control_protocol,
    address=config.zmq_pub_control_address,
)
settings_selector = SettingsSelector(state_store=store,
    settings_publisher=settings_publisher,
    interval=config.leader_rotation_interval,
)
metrics_collector = MetricsCollector(state_store=store,
    protocol=config.zmq_pull_metrics_protocol,
    address=config.zmq_pull_metrics_address,
)
prom_http_server = PrometheusHttpServer(lambda: store)

def start_threads():
    prom_http_server.start()
    metrics_collector.start()
    settings_selector.start()

def stop_threads():
    settings_publisher.close()
    settings_selector.stop()
    metrics_collector.stop()
    prom_http_server.stop()

app = FastAPI(
    on_startup=[start_threads],
    on_shutdown=[stop_threads],
)

@app.get("/metrics")
def get_metrics():
    return store.dict()

@app.get("/")
def root():
    return {"status": "Dashcorn dashboard running"}
