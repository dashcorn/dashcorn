import zmq
import json

ctx = zmq.Context()
sock = ctx.socket(zmq.PUSH)
sock.connect("tcp://127.0.0.1:5556")  # Dashboard server

def send_metric(data: dict):
    try:
        sock.send_json(data)
    except Exception as e:
        print("ZMQ send error:", e)
