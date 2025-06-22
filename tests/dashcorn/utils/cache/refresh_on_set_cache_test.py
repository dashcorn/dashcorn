import time
import pytest

from dashcorn.utils.cache.refresh_on_set_cache import RefreshOnSetCache

def test_basic_set_get():
    cache = RefreshOnSetCache(ttl=2)
    cache["a"] = 1
    assert cache["a"] == 1

def test_expire_after_ttl():
    cache = RefreshOnSetCache(ttl=0.1)
    cache["a"] = 1
    time.sleep(0.2)
    with pytest.raises(KeyError):
        _ = cache["a"]

def test_ttl_not_reset_on_get():
    cache = RefreshOnSetCache(ttl=0.3)
    cache["a"] = 1
    time.sleep(0.2)
    _ = cache["a"]  # access does not reset TTL
    time.sleep(0.2)
    with pytest.raises(KeyError):
        _ = cache["a"]

def test_ttl_reset_on_set():
    cache = RefreshOnSetCache(ttl=0.3)
    cache["a"] = 1
    time.sleep(0.2)
    cache["a"] = 2  # reset TTL
    time.sleep(0.2)
    assert cache["a"] == 2

def test_expire_callback_called():
    called = []

    def on_expire(key, value):
        called.append((key, value))

    cache = RefreshOnSetCache(ttl=0.1, on_expire=on_expire)
    cache["a"] = "hello"
    time.sleep(0.2)
    with pytest.raises(KeyError):
        _ = cache["a"]
    assert called == [("a", "hello")]

def test_auto_cleanup():
    seen = []

    def on_expire(key, value):
        seen.append(key)

    cache = RefreshOnSetCache(ttl=0.1, on_expire=on_expire, cleanup_interval=0.05)
    cache["x"] = 10
    time.sleep(0.3)
    assert "x" in seen
    cache.stop_auto_cleanup()

def test_update_and_pop():
    cache = RefreshOnSetCache(ttl=5)
    cache.update({"a": 1, "b": 2})
    assert cache["a"] == 1
    assert cache["b"] == 2

    popped = cache.pop("a")
    assert popped == 1
    assert "a" not in cache

def test_setdefault_behavior():
    cache = RefreshOnSetCache(ttl=5)
    val = cache.setdefault("x", 100)
    assert val == 100
    assert cache["x"] == 100

    val2 = cache.setdefault("x", 200)
    assert val2 == 100  # không thay đổi nếu đã tồn tại

def test_clear_works():
    cache = RefreshOnSetCache(ttl=5)
    cache["x"] = 1
    cache["y"] = 2
    cache.clear()
    assert len(cache) == 0

def test_repr_debug():
    cache = RefreshOnSetCache(ttl=5)
    cache["a"] = 1
    r = repr(cache)
    assert "ttl=" in r and "size=1" in r

def test_copy_creates_independent_copy():
    cache = RefreshOnSetCache(ttl=5)
    cache["a"] = 123
    cache2 = cache.copy()
    assert cache2["a"] == 123
    cache2["a"] = 456
    assert cache["a"] != cache2["a"]

def test_maxlen_eviction():
    expired = []

    def on_expire(k, v):
        expired.append(k)

    cache = RefreshOnSetCache(ttl=5, maxlen=2, on_expire=on_expire)
    cache["a"] = 1
    cache["b"] = 2
    cache["c"] = 3  # sẽ đẩy a ra

    assert "a" not in cache
    assert expired == ["a"]
