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
"""

import os
import psutil
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware

from .worker_sender import MetricsSender
from .settings_store import SettingsStore
from .settings_listener import SettingsListener
from .worker_reporter import WorkerReporter

logger = logging.getLogger(__name__)

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

    def __init__(self, app):
        """
        Initialize the MetricsMiddleware.

        This sets up the middleware to intercept HTTP requests and also starts
        a background system metrics reporter that periodically collects and sends
        system-level metrics (e.g., CPU, memory).

        Args:
            app (ASGIApp): The ASGI application instance to wrap with the middleware.

        Side Effects:
            - Starts a background thread or task that sends system metrics every 5 seconds.
        """
        super().__init__(app)

        self._pid = os.getpid()
        self._parent_pid = psutil.Process(self._pid).ppid()

        logger.debug(f"👷 [{self.__class__.__name__}] PID: {self._pid}, Parent PID: {self._parent_pid}")

        self._settings_store = SettingsStore()

        self._settings_listener = SettingsListener(port=5557,
                handle_message=self._settings_store.update_settings)
        self._settings_listener.start()

        self._metrics_sender = MetricsSender(port=5556)

        self._worker_reporter = WorkerReporter(interval=4.0,
            settings_store=self._settings_store,
            metrics_sender=self._metrics_sender)
        self._worker_reporter.start()

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

        self._metrics_sender.send({
            "type": "http",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration": duration,
            "time": time.time(),
            "pid": self._pid,
            "parent_pid": self._parent_pid,
        })

        return response
