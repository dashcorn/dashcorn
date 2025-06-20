from fastapi import FastAPI
from dashcorn.agent.middleware import MetricsMiddleware

app = FastAPI()
app.add_middleware(MetricsMiddleware)

@app.get("/")
async def root():
    return {"message": "Hello World"}
