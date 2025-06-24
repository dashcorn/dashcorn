import time
from collections.abc import MutableMapping
from typing import Any, Iterator

class ExpireIfIdleDict(MutableMapping):
    def __init__(self, ttl: float = 60.0):
        self._store: dict[Any, Any] = {}
        self._ttl = ttl
        self._last_write = time.monotonic()

    def _touch(self):
        self._last_write = time.monotonic()

    def _maybe_expire(self):
        if time.monotonic() - self._last_write >= self._ttl:
            self._store.clear()

    # --- MutableMapping interface ---
    def __setitem__(self, key: Any, value: Any) -> None:
        self._maybe_expire()
        self._store[key] = value
        self._touch()

    def __getitem__(self, key: Any) -> Any:
        self._maybe_expire()
        return self._store[key]

    def __delitem__(self, key: Any) -> None:
        self._maybe_expire()
        del self._store[key]
        self._touch()

    def __iter__(self) -> Iterator:
        self._maybe_expire()
        return iter(self._store.copy())

    def __len__(self) -> int:
        self._maybe_expire()
        return len(self._store)

    def clear(self) -> None:
        self._store.clear()
        self._touch()

    def update(self, *args, **kwargs) -> None:
        self._maybe_expire()
        self._store.update(*args, **kwargs)
        self._touch()

    def __repr__(self) -> str:
        self._maybe_expire()
        return f"{self.__class__.__name__}({self._store})"
