from fastapi import FastAPI

import dashcorn.utils.logging

from dashcorn.hub.hooks import store, start_threads, stop_threads

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
