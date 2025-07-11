import time
import threading
from collections.abc import MutableMapping
from collections import OrderedDict
from typing import Any, Callable, Optional, Iterator, Tuple

T = Any
K = Any
V = Any
ExpireCallback = Optional[Callable[[K, V], None]]

class RefreshOnSetCache(MutableMapping[K, V]):
    def __init__(
        self,
        ttl: float,
        maxlen: Optional[int] = None,
        on_expire: ExpireCallback = None,
        cleanup_interval: Optional[float] = None,
    ) -> None:
        self._ttl: float = ttl
        self._maxlen: Optional[int] = maxlen
        self._store: OrderedDict[K, Tuple[V, float]] = OrderedDict()
        self._on_expire: ExpireCallback = on_expire
        self._cleanup_interval = cleanup_interval
        self._cleanup_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._timer_thread: Optional[threading.Timer] = None

        if cleanup_interval:
            self._start_auto_cleanup()

    def __setitem__(self, key: K, value: V) -> None:
        with self._cleanup_lock:
            now = time.monotonic()
            self._store[key] = (value, now)
            self._store.move_to_end(key)
            self._evict_if_needed()

    def _evict_if_needed(self) -> None:
        if self._maxlen is not None:
            while len(self._store) > self._maxlen:
                k, (v, _) = self._store.popitem(last=False) # last ~ LIFO
                if self._on_expire:
                    try:
                        self._on_expire(k, v)
                    except Exception:
                        pass

    def copy(self) -> "RefreshOnSetCache[K, V]":
        with self._cleanup_lock:
            new_cache = RefreshOnSetCache(
                ttl=self._ttl,
                on_expire=self._on_expire,
                cleanup_interval=self._cleanup_interval,
                maxlen=self._maxlen
            )
            new_cache._store = OrderedDict(self._store.copy())
            return new_cache

    def __repr__(self) -> str:
        self._cleanup()
        keys = list(self._store.keys())
        return f"<RefreshOnSetCache ttl={self._ttl}s size={len(self._store)} keys={keys}>"

    def __getitem__(self, key: K) -> V:
        with self._cleanup_lock:
            value, set_time = self._store[key]
            if time.monotonic() - set_time > self._ttl:
                self._expire_key(key, value)
                raise KeyError(f"{key} has expired")
            return value

    def __delitem__(self, key: K) -> None:
        with self._cleanup_lock:
            del self._store[key]

    def __iter__(self) -> Iterator[K]:
        self._cleanup()
        return iter(self._store)

    def __len__(self) -> int:
        self._cleanup()
        return len(self._store)

    def _expire_key(self, key: K, value: V) -> None:
        del self._store[key]
        if self._on_expire:
            try:
                self._on_expire(key, value)
            except Exception:
                pass  # không làm crash cache nếu callback lỗi

    def _cleanup(self) -> None:
        now = time.monotonic()
        expired = []
        with self._cleanup_lock:
            for key, (value, set_time) in list(self._store.items()):
                if now - set_time > self._ttl:
                    expired.append((key, value))
            for key, value in expired:
                self._expire_key(key, value)

    def _start_auto_cleanup(self) -> None:
        if self._stop_event.is_set():
            return
        self._cleanup()
        self._timer_thread = threading.Timer(
            self._cleanup_interval, self._start_auto_cleanup
        )
        self._timer_thread.daemon = True
        self._timer_thread.start()

    def stop_auto_cleanup(self) -> None:
        self._stop_event.set()
        if self._timer_thread:
            self._timer_thread.cancel()

    def keys(self) -> Iterator[K]:
        self._cleanup()
        return self._store.keys()

    def items(self) -> Iterator[Tuple[K, V]]:
        self._cleanup()
        return ((k, v[0]) for k, v in self._store.items())

    def values(self) -> Iterator[V]:
        self._cleanup()
        return (v[0] for v in self._store.values())

    def get_set_time(self, key: K) -> Optional[float]:
        if key in self._store:
            return self._store[key][1]
        return None
    
    def update(self, other=None, **kwargs):
        if other:
            if isinstance(other, dict):
                for k, v in other.items():
                    self[k] = v
            else:
                for k, v in other:
                    self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    def setdefault(self, key: K, default: V) -> V:
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    def pop(self, key: K, default: Optional[V] = None) -> V:
        try:
            value = self[key]  # may raise KeyError (expired)
            del self[key]
            return value
        except KeyError:
            if default is not None:
                return default
            raise

    def clear(self):
        with self._cleanup_lock:
            self._store.clear()


if __name__ == "__main__":
    import time

    def on_expire_demo(key, value):
        print(f"🔥 {key} expired with value = {value}")

    cache = RefreshOnSetCache(ttl=3, on_expire=on_expire_demo, cleanup_interval=1.0)

    cache["a"] = 1
    cache["b"] = 2

    time.sleep(2)
    cache["a"] = 11  # reset TTL → không expired

    time.sleep(2)
    # b sẽ hết hạn vì không được cập nhật
    # a vẫn tồn tại

    print("Final keys:", list(cache.keys()))

    cache.stop_auto_cleanup()
