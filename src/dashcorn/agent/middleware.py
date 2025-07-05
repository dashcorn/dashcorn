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
import uuid

from collections.abc import Iterable
from typing import Awaitable, Callable, Optional

from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from dashcorn.commons.agent_info_util import get_agent_id

from .config import AgentConfig
from .worker_sender import MetricsSender
from .settings_store import SettingsStore
from .settings_listener import SettingsListener
from .worker_reporter import WorkerReporter

X_REQUEST_ID = "X-Request-Id"

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

    def __init__(self, app, *args, config: Optional[AgentConfig]=None,
            enable_request_id: bool = True,
            normalize_path: Optional[Callable]=None,
            **kwargs):
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
        super().__init__(app, *args, **kwargs)

        self._config = config or AgentConfig()
        self._enable_request_id = enable_request_id
        self._normalize_path = normalize_path

        self._pid = os.getpid()
        self._parent_pid = psutil.Process(self._pid).ppid()
        self._agent_id = get_agent_id()

        logger.debug(f"👷 [{self.__class__.__name__}] PID: {self._pid}, Parent PID: {self._parent_pid}")

        self._settings_store = SettingsStore()

        self._settings_listener = SettingsListener(
                address=self._config.zmq_control_address,
                protocol=self._config.zmq_control_protocol,
                handle_message=self._settings_store.update_settings)
        self._settings_listener.start()

        self._metrics_sender = MetricsSender(
                address=self._config.zmq_metrics_address,
                protocol=self._config.zmq_metrics_protocol,
                logging_enabled=self._config.enable_logging)

        self._worker_reporter = WorkerReporter(interval=4.0,
            settings_store=self._settings_store,
            metrics_sender=self._metrics_sender)
        self._worker_reporter.start()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Intercept the HTTP request, measure its processing time, and send metrics.

        Args:
            request (Request): The incoming HTTP request.
            call_next (Callable): The next middleware or route handler to call.

        Returns:
            Response: The HTTP response returned by the next handler.
        """
        start_time = time.perf_counter()
        extras = dict()

        if self._enable_request_id:
            mutable_headers = MutableHeaders(scope=request.scope)

            if "x-request-id" not in mutable_headers:
                mutable_headers["x-request-id"] = str(uuid.uuid4())

            request_id = mutable_headers["x-request-id"]
            request.scope[X_REQUEST_ID] = request_id
            extras["request_id"] = request_id

        try:
            response = await call_next(request)
        except Exception as exc:
            response = Response("Internal Server Error", status_code=500)
            raise exc
        finally:
            if self._enable_request_id:
                if X_REQUEST_ID not in response.headers:
                    response.headers[X_REQUEST_ID] = request_id

            duration = time.perf_counter() - start_time
            self._metrics_sender.send({
                "type": "http",
                "method": request.method,
                "path": get_route_path(request, self._normalize_path),
                "status": response.status_code,
                "duration": duration,
                "time": time.time(),
                "pid": self._pid,
                "parent_pid": self._parent_pid,
                "agent_id": self._agent_id,
                **extras,
            })

        return response

def get_route_path(request: Request, normalize: Optional[Callable]=None, safe_check: bool = True):
    if not safe_check:
        return request.scope.get("route").path if "route" in request.scope else request.url.path

    route_path = None
    if hasattr(request, "scope") and isinstance(request.scope, Iterable):
        route_path = getattr(request.scope.get("route", object()), "path", None)
    if route_path is None:
        if callable(normalize):
            route_path = normalize(request.url.path)
        else:
            route_path = "?"
    return route_path
