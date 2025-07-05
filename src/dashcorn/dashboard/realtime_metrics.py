import logging
import threading

from typing import Any, Dict, List, Literal, Optional

from dashcorn.utils.cache import ExpiringDeque
from dashcorn.utils.cache import ExpireIfIdleDict
from dashcorn.utils.cache import RefreshOnSetCache

logger = logging.getLogger(__name__)

Kind = Literal["http", "server"]

class RealtimeState:
    def __init__(self,
            http_event_ttl: Optional[float] = 60.0,
            http_events_maxlen: Optional[int] = 10000,
            master_ttl: float = 5.0,
            worker_ttl: float = 5.0,
            workers_maxlen: int = 100,
            logging_enabled: bool = False):
        self._http_event_ttl = http_event_ttl
        self._http_events_maxlen = http_events_maxlen
        self._http_events_lock = threading.Lock()
        self._http_events: ExpiringDeque[dict[str, Any]] = ExpiringDeque(
                ttl=self._http_event_ttl,
                maxlen=self._http_events_maxlen)
        self._server_state = {} # dict[str, RefreshOnSetCache[str, dict[str, Any]]] = {}
        self._master_ttl = master_ttl
        self._worker_ttl = worker_ttl
        self._workers_maxlen = workers_maxlen
        self._workers_lock = threading.Lock()
        self._logging_enabled = logging_enabled

    def update(self, kind: Kind, data: dict[str, Any]) -> None:
        if kind == "http":
            with self._http_events_lock:
                if self._logging_enabled:
                    _len1 = len(self._http_events)
                self._http_events.append(data)
                if self._logging_enabled:
                    _len2 = len(self._http_events)
                    logger.debug(f"HTTP event has been appended. Total {_len1} -> {_len2}")

        elif kind == "server":
            agent_id = data.get("agent_id")
            if not agent_id:
                if self._logging_enabled:
                    logger.debug(f"Missing agent_id in server data: {data}")
                return

            if agent_id not in self._server_state:
                self._server_state[agent_id] = {
                    "master": ExpireIfIdleDict(ttl=self._master_ttl),
                    "workers": RefreshOnSetCache(ttl=self._worker_ttl, maxlen=self._workers_maxlen),
                    "last_index": -1,
                }

            _master = data.get("master", {})
            if _master:
                self._server_state[agent_id]["master"].update(_master)

            workers = data.get("workers", {})
            if workers:
                for worker_id, worker_info in workers.items():
                    self._server_state[agent_id]["workers"][worker_id] = worker_info

            if self._logging_enabled:
                logger.debug(f"Server state updated for {agent_id} with {len(workers)} workers")

    def elect_leaders(self) -> List[Dict[str, Any]]:
        """
        Perform round-robin election over current live workers.
        Returns:
            pid of selected worker or None if no candidate found.
        """
        leaders = []

        for agent_id, cache in self._server_state.items():
            heartbeat = cache.get("heartbeat", 0)
            cache["heartbeat"] = heartbeat + 1

            candidates = []
            for worker_id, worker in cache.get("workers",{}).items():
                pid = worker.get("pid")
                if pid:
                    candidates.append(dict(agent_id=agent_id, leader=pid, heartbeat=heartbeat))

            if not candidates:
                logger.debug("No active workers found for leader election.")
                continue

            # Round-robin selection
            _last_index = cache.get("last_index", -1)
            cache["last_index"] = (_last_index + 1) % len(candidates)
            leaders.append(candidates[_last_index])

        return leaders

    def get_http_events(self, cleancut: bool=False) -> list[dict[str, Any]]:
        with self._http_events_lock:
            http_snapshot = list(self._http_events)
            if cleancut:
                self._http_events.clear()
            return http_snapshot

    def get_server_workers(self, agent_id: str) -> dict[str, dict[str, Any]]:
        return self._extract_server_state(self._server_state.get(agent_id))

    def _extract_server_state(self, cache) -> dict[str, dict[str, Any]]:
        return {
            "master": cache.get("master", {}),
            "workers": {
                worker_id: worker_data
                for worker_id, worker_data in cache.get("workers", {}).items()
            }
        } if cache else {}

    def get_all_servers(self) -> dict[str, dict[str, dict[str, Any]]]:
        return {
            agent_id: self._extract_server_state(cache)
            for agent_id, cache in self._server_state.items()
        }

    def dict(self):
        return {
            "http": self.get_http_events(),
            "server": self.get_all_servers(),
        }
