from fastapi import FastAPI

from dashcorn.dashboard.realtime_metrics import RealtimeState
from dashcorn.dashboard.settings_selector import SettingsSelector
from dashcorn.dashboard.settings_publisher import SettingsPublisher
from dashcorn.dashboard.metrics_collector import MetricsCollector

import dashcorn.utils.logging

store = RealtimeState()

settings_publisher = SettingsPublisher()
settings_selector = SettingsSelector(state_store=store, settings_publisher=settings_publisher)
metrics_collector = MetricsCollector(state_store=store)

def start_threads():
    metrics_collector.start()
    settings_selector.start()

def stop_threads():
    settings_publisher.close()
    settings_selector.stop()
    metrics_collector.stop()

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
