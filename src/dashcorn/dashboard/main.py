from fastapi import FastAPI

from dashcorn.dashboard.realtime_metrics import store
from dashcorn.dashboard.settings_publisher import SettingsPublisher
from dashcorn.dashboard.metrics_collector import MetricsCollector

import dashcorn.utils.logging

app = FastAPI()

settings_publisher = SettingsPublisher()
metrics_collector = MetricsCollector()

metrics_collector.start()

@app.get("/metrics")
def get_metrics():
    return store.dict()

@app.get("/")
def root():
    return {"status": "Dashcorn dashboard running"}
