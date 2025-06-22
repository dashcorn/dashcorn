import time
import threading
from collections.abc import MutableMapping
from typing import Callable, Optional, Any

class ExpireOnSetCache(MutableMapping):
    def __init__(
        self,
        ttl: float,
        on_expire: Optional[Callable[[Any, Any], None]] = None,
        cleanup_interval: Optional[float] = None
    ):
        """
        :param ttl: thời gian tồn tại (giây) kể từ lần `set()`
        :param on_expire: callback(key, value) khi phần tử bị expire
        :param cleanup_interval: nếu đặt, sẽ tự động cleanup định kỳ
        """
        self._ttl = ttl
        self._store: dict[Any, tuple[Any, float]] = {}
        self._on_expire = on_expire
        self._cleanup_interval = cleanup_interval
        self._cleanup_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._timer_thread: Optional[threading.Timer] = None

        if cleanup_interval:
            self._start_auto_cleanup()

    def __setitem__(self, key, value):
        with self._cleanup_lock:
            self._store[key] = (value, time.monotonic())

    def __getitem__(self, key):
        with self._cleanup_lock:
            value, set_time = self._store[key]
            if time.monotonic() - set_time > self._ttl:
                self._expire_key(key, value)
                raise KeyError(f"{key} has expired")
            return value

    def __delitem__(self, key):
        with self._cleanup_lock:
            del self._store[key]

    def __iter__(self):
        self._cleanup()
        return iter(self._store)

    def __len__(self):
        self._cleanup()
        return len(self._store)

    def _expire_key(self, key, value):
        del self._store[key]
        if self._on_expire:
            try:
                self._on_expire(key, value)
            except Exception:
                pass  # Không để lỗi callback làm crash cache

    def _cleanup(self):
        now = time.monotonic()
        expired = []
        with self._cleanup_lock:
            for key, (value, set_time) in list(self._store.items()):
                if now - set_time > self._ttl:
                    expired.append((key, value))
            for key, value in expired:
                self._expire_key(key, value)

    def _start_auto_cleanup(self):
        if self._stop_event.is_set():
            return
        self._cleanup()
        self._timer_thread = threading.Timer(
            self._cleanup_interval, self._start_auto_cleanup
        )
        self._timer_thread.daemon = True
        self._timer_thread.start()

    def stop_auto_cleanup(self):
        self._stop_event.set()
        if self._timer_thread:
            self._timer_thread.cancel()

    def keys(self):
        self._cleanup()
        return self._store.keys()

    def items(self):
        self._cleanup()
        return ((k, v[0]) for k, v in self._store.items())

    def values(self):
        self._cleanup()
        return (v[0] for v in self._store.values())

    def get_set_time(self, key):
        if key in self._store:
            return self._store[key][1]
        return None


if __name__ == "__main__":
    import time

    def on_expire_demo(key, value):
        print(f"🔥 {key} expired with value = {value}")

    cache = ExpireOnSetCache(ttl=3, on_expire=on_expire_demo, cleanup_interval=1.0)

    cache["a"] = 1
    cache["b"] = 2

    time.sleep(2)
    cache["a"] = 11  # reset TTL → không expired

    time.sleep(2)
    # b sẽ hết hạn vì không được cập nhật
    # a vẫn tồn tại

    print("Final keys:", list(cache.keys()))

    cache.stop_auto_cleanup()
