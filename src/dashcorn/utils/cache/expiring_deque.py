from collections import deque
from typing import Generic, TypeVar, Deque, List, Optional
import time

T = TypeVar("T")

class ExpiringDeque(Generic[T]):
    """
    A FIFO queue that holds items only for a limited amount of time (TTL).
    Once TTL has passed since insertion, items are automatically purged on access.
    """

    def __init__(self, ttl: Optional[float] = None, maxlen: Optional[int] = None):
        """
        Args:
            ttl (float): Time-to-live in seconds for each item
        """
        self.ttl = ttl
        self.maxlen = maxlen
        self._data: Deque[tuple[float, T]] = deque()

    def append(self, item: T) -> None:
        """
        Add a new item to the queue.
        """
        self._expire_old()
        self._data.append((time.monotonic(), item))
        if self.maxlen and len(self._data) > self.maxlen:
            self._data.popleft()

    def appendleft(self, item: T):
        self._expire_old()
        self._data.appendleft((time.monotonic(), item))
        if self.maxlen and len(self._data) > self.maxlen:
            self._data.pop()

    def _expire_old(self) -> None:
        if self.ttl is None:
            return
        now = time.monotonic()
        while self._data and (now - self._data[0][0] > self.ttl):
            self._data.popleft()

    def get_items(self) -> List[T]:
        """
        Get a list of items that are still within TTL.
        """
        self._expire_old()
        return [item for _, item in self._data]

    def __len__(self) -> int:
        self._expire_old()
        return len(self._data)

    def __iter__(self) -> iter:
        self._expire_old()
        for _, value in self._data:
            yield value

    def clear(self) -> None:
        self._data.clear()

    def __repr__(self) -> str:
        return f"<TTLDeque ttl={self.ttl}s size={len(self)}>"
