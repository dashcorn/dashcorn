from fastapi import FastAPI
from dashcorn.dashboard.zmq_server import start_listener, received_data

app = FastAPI()

start_listener()

@app.get("/metrics")
def get_metrics():
    return received_data[-50:]  # Return last 50 entries

@app.get("/")
def root():
    return {"status": "Dashcorn dashboard running"}
