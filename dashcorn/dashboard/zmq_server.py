"""
zmq_server

A lightweight ZeroMQ server for receiving and printing metrics from distributed
clients (e.g., FastAPI/Gunicorn workers). This module listens on a configurable
TCP port using a PULL socket, collects incoming JSON messages, and stores them
in memory for inspection or further processing.

Functions:
    - zmq_listener(): Blocking loop that listens for incoming JSON messages via ZeroMQ.
    - start_listener(): Launches the listener in a background daemon thread.

Attributes:
    - received_data (List[dict]): In-memory list of all received messages for debugging or testing.

Usage:
    Call `start_listener()` once at application startup or in a script to begin
    receiving metrics.

Example:
    >>> from zmq_server import start_listener
    >>> start_listener()
    >>> # Metrics will be printed to stdout and stored in `received_data`.

Notes:
    - Messages are expected to be sent using ZeroMQ's PUSH pattern (e.g., from zmq_client).
    - This server is intended for development, testing, or prototyping purposes.
    - For production, consider using persistent storage or integrating with a monitoring backend.
"""

import zmq
import threading

received_data = []

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
    sock = ctx.socket(zmq.PULL)
    sock.bind("tcp://*:5556")
    while True:
        msg = sock.recv_json()
        received_data.append(msg)
        print("Received metric:", msg)

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
