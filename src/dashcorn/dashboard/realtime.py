from dashcorn.utils.cache import ExpireOnSetCache

import logging

logger = logging.getLogger(__name__)

# Could be in-memory cache, or WebSocket broadcasting
realtime_state = {
    "http": [],
    "server": {},
}

def update_realtime_view(kind: str, data: dict, log_store_event: bool = False):
    if kind == "http":
        realtime_state["http"].append(data)
        if len(realtime_state["http"]) > 100:
            realtime_state["http"] = realtime_state["http"][-100:]
        if log_store_event:
            logger.debug(f"http event has been appended to realtime_state['http']")
    elif kind == "server":
        hostname = data.get("hostname")
        if not hostname:
            if log_store_event:
                logger.debug(f"data: { data }")
            return
        if hostname not in realtime_state["server"]:
            realtime_state["server"][hostname] = ExpireOnSetCache(ttl=5)
        workers = data.get("workers", {})
        for worker_id, worker in workers.items():
            realtime_state["server"][hostname][worker_id] = worker
        if log_store_event:
            logger.debug(f"server state is updated into realtime_state['server'][{hostname}]")
