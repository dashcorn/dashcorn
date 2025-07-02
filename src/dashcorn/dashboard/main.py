from fastapi import FastAPI

from dashcorn.dashboard.config import DashboardConfig
from dashcorn.dashboard.realtime_metrics import RealtimeState
from dashcorn.dashboard.settings_selector import SettingsSelector
from dashcorn.dashboard.settings_publisher import SettingsPublisher
from dashcorn.dashboard.metrics_collector import MetricsCollector

from dashcorn.dashboard.prom_metrics_exporter import PromMetricsExporter
from dashcorn.dashboard.prom_metrics_scheduler import PromMetricsScheduler
from dashcorn.dashboard.prom_metrics_server import PromMetricsServer

from dashcorn.dashboard.process_executor import ProcessExecutor
from dashcorn.dashboard.process_manager import ProcessManager

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

prom_metrics_exporter = PromMetricsExporter(lambda: store)
prom_metrics_scheduler = PromMetricsScheduler(prom_metrics_exporter)
prom_metrics_server = PromMetricsServer(prom_metrics_exporter)

process_executor = ProcessExecutor()
process_manager = ProcessManager(
    process_executor=process_executor,
)

def start_threads():
    process_manager.start()
    prom_metrics_server.start()
    prom_metrics_scheduler.start()
    metrics_collector.start()
    settings_selector.start()

def stop_threads():
    settings_publisher.close()
    settings_selector.stop()
    metrics_collector.stop()
    prom_metrics_scheduler.stop()
    prom_metrics_server.stop()
    process_manager.stop()

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
