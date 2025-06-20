"""
metrics_middleware

This module provides an ASGI middleware for tracking HTTP request metrics in
Starlette or FastAPI applications. It captures key data about each request such as:

- HTTP method
- Request path
- Response status code
- Processing duration (in seconds)
- Timestamp when the request completed

The collected metrics are sent using ZeroMQ to a monitoring server via the `send_metric`
function, defined in the `zmq_client` module.

Classes:
    - MetricsMiddleware: A subclass of Starlette's BaseHTTPMiddleware that wraps
      incoming requests to log and forward timing metrics.

Example:
    from metrics_middleware import MetricsMiddleware

    app.add_middleware(MetricsMiddleware)

Dependencies:
    - time: For high-resolution duration measurement and timestamps.
    - starlette.middleware.base.BaseHTTPMiddleware: For ASGI middleware structure.
    - zmq_client.send_metric: For sending metrics to an external observer.

This middleware is intended for use in performance monitoring, request tracking,
and operational observability.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from .zmq_client import send_metric

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware for collecting and sending HTTP request metrics.

    This middleware measures the duration of each HTTP request and sends
    a structured metric including method, path, status code, response time,
    and timestamp. It is useful for monitoring performance and request patterns
    in web applications.

    Metrics are sent using the `send_metric` function from the zmq_client module.

    Attributes:
        Inherits from BaseHTTPMiddleware and overrides the `dispatch` method.
    """

    async def dispatch(self, request, call_next):
        """
        Intercept the HTTP request, measure its processing time, and send metrics.

        Args:
            request (Request): The incoming HTTP request.
            call_next (Callable): The next middleware or route handler to call.

        Returns:
            Response: The HTTP response returned by the next handler.
        """
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
