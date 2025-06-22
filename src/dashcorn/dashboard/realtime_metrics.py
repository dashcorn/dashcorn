import logging

from typing import Any, Literal
from collections import deque

from dashcorn.utils.cache import ExpireOnSetCache

logger = logging.getLogger(__name__)

Kind = Literal["http", "server"]

class RealtimeState:
    def __init__(self, max_http_events: int = 100, worker_ttl: float = 5.0):
        self._http_events: deque[dict[str, Any]] = deque(maxlen=max_http_events)
        self._max_http_events = max_http_events
        self._server_state: dict[str, ExpireOnSetCache[str, dict[str, Any]]] = {}
        self._worker_ttl = worker_ttl

    def update(self, kind: Kind, data: dict[str, Any], log_store_event: bool = False) -> None:
        if kind == "http":
            self._http_events.append(data)
            if log_store_event:
                logger.debug(f"HTTP event has been appended. Total = {len(self._http_events)}")

        elif kind == "server":
            hostname = data.get("hostname")
            if not hostname:
                if log_store_event:
                    logger.debug(f"Missing hostname in server data: {data}")
                return

            if hostname not in self._server_state:
                self._server_state[hostname] = ExpireOnSetCache(ttl=self._worker_ttl)

            workers = data.get("workers", {})
            for worker_id, worker_info in workers.items():
                self._server_state[hostname][worker_id] = worker_info

            if log_store_event:
                logger.debug(f"Server state updated for {hostname} with {len(workers)} workers")

    def get_http_events(self) -> list[dict[str, Any]]:
        return list(self._http_events)

    def get_server_workers(self, hostname: str) -> dict[str, dict[str, Any]]:
        cache = self._server_state.get(hostname)
        if not cache:
            return {}
        return {k: v for k, v in cache.items()}

    def get_all_servers(self) -> dict[str, dict[str, dict[str, Any]]]:
        return {
            hostname: {
                "workers": {
                    worker_id: worker_data
                    for worker_id, worker_data in cache.items()
                }
            }
            for hostname, cache in self._server_state.items()
        }

    def dict(self):
        return {
            "http": self.get_http_events(),
            "server": self.get_all_servers(),
        }

store = RealtimeState()
