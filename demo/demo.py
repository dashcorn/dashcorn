from typing import Optional
from fastapi import FastAPI, Header

from dashcorn.agent.config import AgentConfig
from dashcorn.agent.middleware import MetricsMiddleware

import dashcorn.utils.logging

app = FastAPI()

app.add_middleware(MetricsMiddleware)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/users/{user_id}")
async def get_user(user_id: str, x_request_id: Optional[str] = Header(None)):
    return {
        "id": user_id,
        "x-request-id": x_request_id,
    }
