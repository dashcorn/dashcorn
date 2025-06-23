import logging

from typing import Any, Dict, List, Literal, Optional

from dashcorn.utils.cache import ExpiringDeque
from dashcorn.utils.cache import RefreshOnSetCache

logger = logging.getLogger(__name__)

Kind = Literal["http", "server"]

class RealtimeState:
    def __init__(self,
            http_event_ttl: Optional[float] = 60.0,
            http_events_maxlen: Optional[int] = 10000,
            worker_ttl: float = 5.0,
            workers_maxlen: int = 100,
            log_store_event: bool = False):
        self._http_event_ttl = http_event_ttl
        self._http_events_maxlen = http_events_maxlen
        self._http_events: ExpiringDeque[dict[str, Any]] = ExpiringDeque(
                ttl=self._http_event_ttl,
                maxlen=self._http_events_maxlen)
        self._server_state = {} # dict[str, RefreshOnSetCache[str, dict[str, Any]]] = {}
        self._worker_ttl = worker_ttl
        self._workers_maxlen = workers_maxlen
        self._log_store_event = log_store_event

    def update(self, kind: Kind, data: dict[str, Any]) -> None:
        if kind == "http":
            self._http_events.append(data)
            if self._log_store_event:
                logger.debug(f"HTTP event has been appended. Total = {len(self._http_events)}")

        elif kind == "server":
            hostname = data.get("hostname")
            if not hostname:
                if self._log_store_event:
                    logger.debug(f"Missing hostname in server data: {data}")
                return

            if hostname not in self._server_state:
                self._server_state[hostname] = {
                    "master": {},
                    "workers": RefreshOnSetCache(ttl=self._worker_ttl, maxlen=self._workers_maxlen),
                    "last_index": -1,
                }

            _master = data.get("master", None)
            if _master:
                self._server_state[hostname]["master"] = _master

            workers = data.get("workers", {})
            if workers:
                for worker_id, worker_info in workers.items():
                    self._server_state[hostname]["workers"][worker_id] = worker_info

            if self._log_store_event:
                logger.debug(f"Server state updated for {hostname} with {len(workers)} workers")

    def elect_leaders(self) -> List[Dict[str, Any]]:
        """
        Perform round-robin election over current live workers.
        Returns:
            pid of selected worker or None if no candidate found.
        """
        leaders = []

        for hostname, cache in self._server_state.items():
            candidates = []
            for worker_id, worker in cache.get("workers",{}).items():
                pid = worker.get("pid")
                if pid:
                    candidates.append(dict(hostname=hostname, leader=pid))

            if not candidates:
                logger.debug("No active workers found for leader election.")
                continue

            # Round-robin selection
            _last_index = cache.get("last_index", -1)
            cache["last_index"] = (_last_index + 1) % len(candidates)
            leaders.append(candidates[_last_index])

        return leaders

    def get_http_events(self) -> list[dict[str, Any]]:
        return list(self._http_events)

    def get_server_workers(self, hostname: str) -> dict[str, dict[str, Any]]:
        cache = self._server_state.get(hostname)
        return {
            "master": cache.get("master", {}),
            "workers": {
                worker_id: worker_data
                for worker_id, worker_data in cache.get("workers", {}).items()
            }
        } if cache else {}

    def get_all_servers(self) -> dict[str, dict[str, dict[str, Any]]]:
        return {
            hostname: {
                "master": cache.get("master", {}),
                "workers": {
                    worker_id: worker_data
                    for worker_id, worker_data in cache.get("workers", {}).items()
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
