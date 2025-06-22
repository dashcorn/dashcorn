import time
import pytest

from dashcorn.utils.cache.expire_on_set_cache import ExpireOnSetCache

def test_basic_set_get():
    cache = ExpireOnSetCache(ttl=2)
    cache["a"] = 1
    assert cache["a"] == 1

def test_expire_after_ttl():
    cache = ExpireOnSetCache(ttl=0.1)
    cache["a"] = 1
    time.sleep(0.2)
    with pytest.raises(KeyError):
        _ = cache["a"]

def test_ttl_not_reset_on_get():
    cache = ExpireOnSetCache(ttl=0.3)
    cache["a"] = 1
    time.sleep(0.2)
    _ = cache["a"]  # access does not reset TTL
    time.sleep(0.2)
    with pytest.raises(KeyError):
        _ = cache["a"]

def test_ttl_reset_on_set():
    cache = ExpireOnSetCache(ttl=0.3)
    cache["a"] = 1
    time.sleep(0.2)
    cache["a"] = 2  # reset TTL
    time.sleep(0.2)
    assert cache["a"] == 2

def test_expire_callback_called():
    called = []

    def on_expire(key, value):
        called.append((key, value))

    cache = ExpireOnSetCache(ttl=0.1, on_expire=on_expire)
    cache["a"] = "hello"
    time.sleep(0.2)
    with pytest.raises(KeyError):
        _ = cache["a"]
    assert called == [("a", "hello")]

def test_auto_cleanup():
    seen = []

    def on_expire(key, value):
        seen.append(key)

    cache = ExpireOnSetCache(ttl=0.1, on_expire=on_expire, cleanup_interval=0.05)
    cache["x"] = 10
    time.sleep(0.3)
    assert "x" in seen
    cache.stop_auto_cleanup()
