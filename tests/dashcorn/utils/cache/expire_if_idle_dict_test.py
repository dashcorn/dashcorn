import time

from dashcorn.utils.cache.expire_if_idle_dict import ExpireIfIdleDict

def test_dict_behavior():
    d = ExpireIfIdleDict(ttl=2)
    d["a"] = 1
    d["b"] = 2

    assert d["a"] == 1
    assert d.get("b") == 2
    assert len(d) == 2
    assert "a" in d

    del d["a"]
    assert "a" not in d

    d.update({"c": 3})
    assert d["c"] == 3

    keys = list(d.keys())
    values = list(d.values())
    items = list(d.items())

    assert "b" in keys
    assert 2 in values
    assert ("b", 2) in items

    d.clear()
    assert len(d) == 0

def test_expiry_if_idle():
    d = ExpireIfIdleDict(ttl=1.0)
    d["x"] = 123

    time.sleep(0.5)
    d["y"] = 456  # reset TTL

    time.sleep(0.5)
    assert "x" in d
    assert "y" in d

    time.sleep(1.2)  # idle > ttl
    assert len(d) == 0
