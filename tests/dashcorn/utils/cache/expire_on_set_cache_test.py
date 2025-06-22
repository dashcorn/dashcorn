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

def test_update_and_pop():
    cache = ExpireOnSetCache(ttl=5)
    cache.update({"a": 1, "b": 2})
    assert cache["a"] == 1
    assert cache["b"] == 2

    popped = cache.pop("a")
    assert popped == 1
    assert "a" not in cache

def test_setdefault_behavior():
    cache = ExpireOnSetCache(ttl=5)
    val = cache.setdefault("x", 100)
    assert val == 100
    assert cache["x"] == 100

    val2 = cache.setdefault("x", 200)
    assert val2 == 100  # không thay đổi nếu đã tồn tại

def test_clear_works():
    cache = ExpireOnSetCache(ttl=5)
    cache["x"] = 1
    cache["y"] = 2
    cache.clear()
    assert len(cache) == 0
