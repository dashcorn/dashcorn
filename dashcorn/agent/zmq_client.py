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
