"""
zmq_server.py

This module provides a ZeroMQ-based listener for receiving real-time metrics
from distributed agents. It is designed to work as part of the Dashcorn dashboard
backend and supports asynchronous processing of various metric types including
worker status and HTTP request data.

Main Components:
----------------
- `zmq_listener()`: A blocking loop that binds to a ZeroMQ socket and receives JSON-formatted metrics.
- `handle_message(msg)`: Dispatches incoming messages based on their type and updates the dashboard.
- `start_listener()`: Starts the listener in a background daemon thread.

Usage:
------
Call `start_listener()` during application startup to enable real-time metric collection.

ZeroMQ Configuration:
---------------------
- Protocol: PULL socket
- Bind Address: tcp://*:5556
- Agents should connect via PUSH socket to this address.

Dependencies:
-------------
- zmq: ZeroMQ for messaging
- threading: For running the listener in a background thread
- json: To parse incoming messages
- dashcorn.dashboard.db: Handles metric persistence
- dashcorn.dashboard.realtime: Updates frontend views
"""

import zmq
import threading
import json

from dashcorn.dashboard import db
from dashcorn.dashboard.realtime import update_realtime_view

ZMQ_BIND_ADDR = "tcp://*:5556"

def handle_message(msg: dict):
    msg_type = msg.get("type")
    if msg_type == "worker_status":
        db.save_worker_info(msg)
        update_realtime_view("worker", msg)
    elif msg_type == "http":
        db.save_http_metric(msg)
        update_realtime_view("http", msg)
    else:
        print(f"[ZMQ] Unknown message type: {msg_type}")

def zmq_listener():
    """
    Blocking loop that listens for incoming metrics via ZeroMQ.

    This function sets up a PULL socket bound to port 5556, waits for
    incoming JSON messages, appends them to the `received_data` list,
    and prints them to stdout.

    Note:
        - This function runs indefinitely and is intended to be run in a background thread.
        - Uses the global `received_data` list to store received messages.
    """
    ctx = zmq.Context()
    socket = ctx.socket(zmq.PULL)
    socket.bind(ZMQ_BIND_ADDR)
    print(f"[ZMQ] Listening on {ZMQ_BIND_ADDR}...")

    while True:
        try:
            raw = socket.recv()
            msg = json.loads(raw)
            handle_message(msg)
        except Exception as e:
            print("[ZMQ] Error while receiving or processing message:", e)


def start_listener():
    """
    Start the ZeroMQ listener in a background daemon thread.

    This function launches `zmq_listener()` on a separate thread so that it can
    run concurrently with the main application without blocking execution.

    Use this function to enable passive metric collection without interfering
    with other parts of your system.
    """
    thread = threading.Thread(target=zmq_listener, daemon=True)
    thread.start()
