from fastapi import FastAPI
from dashcorn.dashboard.db import init_db
from dashcorn.dashboard.realtime_metrics import store
from dashcorn.dashboard.zmq_server import start_listener

import dashcorn.utils.logging

app = FastAPI()

init_db()
start_listener()

@app.get("/metrics")
def get_metrics():
    return store.dict()

@app.get("/")
def root():
    return {"status": "Dashcorn dashboard running"}
