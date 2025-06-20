import zmq
import threading

received_data = []

def zmq_listener():
    ctx = zmq.Context()
    sock = ctx.socket(zmq.PULL)
    sock.bind("tcp://*:5556")
    print(f"server listening at *:5556")
    while True:
        msg = sock.recv_json()
        received_data.append(msg)
        print("Received metric:", msg)

def start_listener():
    thread = threading.Thread(target=zmq_listener, daemon=True)
    thread.start()
