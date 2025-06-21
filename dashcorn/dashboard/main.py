from fastapi import FastAPI
from dashcorn.dashboard.db import init_db
from dashcorn.dashboard.zmq_server import start_listener

app = FastAPI()

init_db()
start_listener()

@app.get("/metrics")
def get_metrics():
    from dashcorn.dashboard.realtime import realtime_state
    return realtime_state

@app.get("/")
def root():
    return {"status": "Dashcorn dashboard running"}
