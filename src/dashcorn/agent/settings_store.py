from dataclasses import dataclass, field
from typing import Optional
import time

from dashcorn.commons.agent_info_util import get_agent_id

@dataclass
class SettingsStore:
    """
    A simple configuration container for Dashcorn agents or dashboard.

    This class keeps track of the current worker PID elected as the leader,
    which is responsible for gathering master process metrics.

    Attributes:
        leader (Optional[int]): The PID of the current leader worker.
        leader_since (float): The timestamp (in seconds since epoch) when the leader was assigned.
    """
    leader: Optional[int] = None
    leader_since: float = field(default_factory=lambda: time.time())
    agent_id: str = field(default_factory=lambda: get_agent_id())
    heartbeat: Optional[int] = None

    def update_leader(self, pid: int):
        """
        Assigns a new leader by PID and updates the timestamp.

        Args:
            pid (int): The process ID (PID) of the worker to be elected as leader.
        """
        self.leader = pid
        self.leader_since = time.time()

    def is_leader_valid(self, ttl: float) -> bool:
        """
        Checks whether the current leader is still valid within a given TTL (time-to-live).

        Args:
            ttl (float): The maximum allowed age of the current leader (in seconds).

        Returns:
            bool: True if the leader is still within the TTL window, False if expired or unset.
        """
        if self.leader is None:
            return False
        return (time.time() - self.leader_since) < ttl

    def update_settings(self, data):
        if not isinstance(data, dict):
            return
        _agent_id = data.get("agent_id", None)
        _leader = data.get("leader", None)
        if _leader and self.agent_id == _agent_id:
            self.update_leader(_leader)
        if self.agent_id == _agent_id:
            heartbeat = data.get("heartbeat", None)
            if heartbeat:
                self.heartbeat = heartbeat
