"""
zmq_client

This module provides a simple ZeroMQ-based client for sending structured
metric data to a monitoring server or dashboard.

It uses a PUSH socket to connect to a predefined ZeroMQ endpoint
(currently `tcp://127.0.0.1:5556`) and sends JSON-encoded metrics.

This module is typically used by ASGI middleware, system reporters, or
other components that need to emit runtime metrics such as request logs,
resource usage, or custom events.

Functions:
    - send_metric(data: dict): Send a JSON-serializable metric dictionary over ZeroMQ.

Global State:
    - ctx (zmq.Context): The ZeroMQ context.
    - sock (zmq.Socket): A PUSH socket connected to the dashboard server.

Usage Example:
    from zmq_client import send_metric

    send_metric({
        "type": "http",
        "method": "POST",
        "path": "/login",
        "status": 200,
        "duration": 0.456,
        "time": 1718881234.567
    })

Notes:
    - This module is designed for fire-and-forget metric reporting.
    - For reliability in production, consider adding retries or persistent queues.
"""

import zmq
import json

ctx = zmq.Context()
sock = ctx.socket(zmq.PUSH)
sock.connect("tcp://127.0.0.1:5556")  # Dashboard server

def send_metric(data: dict):
    """
    Send a metric to the monitoring or dashboard server via ZeroMQ.

    This function serializes the given dictionary as JSON and sends it
    over a PUSH socket to a pre-configured ZeroMQ endpoint (e.g., tcp://127.0.0.1:5556).
    It is typically used to report runtime metrics such as HTTP requests,
    performance data, or other custom telemetry.

    Args:
        data (dict): A dictionary representing the metric to be sent.
                     It should be JSON-serializable.

    Example:
        send_metric({
            "type": "http",
            "method": "GET",
            "path": "/api",
            "status": 200,
            "duration": 0.123,
            "time": 1718880000.123
        })

    Notes:
        If sending fails, the exception is caught and printed to stderr.
        No retry or queue mechanism is implemented.

    Raises:
        None
    """
    try:
        sock.send_json(data)
    except Exception as e:
        print("ZMQ send error:", e)
