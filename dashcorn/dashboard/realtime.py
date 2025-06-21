# Could be in-memory cache, or WebSocket broadcasting

realtime_state = {
    "http": [],
    "worker": {}
}

def update_realtime_view(kind: str, data: dict):
    if kind == "http":
        realtime_state["http"].append(data)
        if len(realtime_state["http"]) > 100:
            realtime_state["http"] = realtime_state["http"][-100:]
    elif kind == "worker":
        hostname = data.get("hostname")
        if hostname:
            realtime_state["worker"][hostname] = data
