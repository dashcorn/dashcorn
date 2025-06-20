import time
from starlette.middleware.base import BaseHTTPMiddleware
from .zmq_client import send_metric

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time

        send_metric({
            "type": "http",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration": duration,
            "time": time.time(),
        })

        return response
