import time

from dashcorn.utils.cache.expiring_deque import ExpiringDeque

def test_deque_keeps_items_within_ttl():
    q = ExpiringDeque(ttl=1.0)
    q.append("A")
    time.sleep(0.5)
    q.append("B")
    assert q.get_items() == ["A", "B"]
    time.sleep(0.6)
    assert q.get_items() == ["B"]
    assert len(q) == 1

def test_clear():
    q = ExpiringDeque(ttl=5)
    q.append("X")
    q.clear()
    assert len(q) == 0
    assert q.get_items() == []

def test_repr():
    q = ExpiringDeque(ttl=3)
    q.append("x")
    assert "ttl=3" in repr(q)
