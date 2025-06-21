import time
from collections.abc import MutableMapping

class ExpireOnSetCache(MutableMapping):
    def __init__(self, ttl: float):
        self._store = {}      # key: (value, last_set_time)
        self._ttl = ttl

    def __setitem__(self, key, value):
        self._store[key] = (value, time.monotonic())

    def __getitem__(self, key):
        value, set_time = self._store[key]
        if time.monotonic() - set_time > self._ttl:
            del self._store[key]
            raise KeyError(f"{key} has expired")
        return value

    def __delitem__(self, key):
        del self._store[key]

    def __iter__(self):
        self._cleanup()
        return iter(self._store)

    def __len__(self):
        self._cleanup()
        return len(self._store)

    def _cleanup(self):
        now = time.monotonic()
        expired = [key for key, (_, set_time) in self._store.items() if now - set_time > self._ttl]
        for key in expired:
            del self._store[key]

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
    cache = ExpireOnSetCache(ttl=5)  # TTL 5s

    key = "worker1"
    cache[key] = {"cpu": 20}

    print(f"{key}: {cache[key]}")  # ✅ OK

    time.sleep(3)
    print(f"{key}: {cache[key]}")  # ✅ vẫn còn

    # chỉ đọc không reset TTL
    time.sleep(3)
    try:
        print(f"{key}: {cache[key]}")  # ❌ expired (6s sau lần set)
    except KeyError:
        print(f"{key} expired")
