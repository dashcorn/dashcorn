import time
import pytest

from dashcorn.dashboard.realtime_metrics import RealtimeState


@pytest.fixture
def realtime():
    return RealtimeState(http_event_ttl=1.0, http_events_maxlen=5, worker_ttl=1.0, workers_maxlen=10)


def test_http_event_append_and_expire(realtime):
    assert realtime.get_http_events() == []

    # Append 3 events
    for i in range(3):
        realtime.update("http", {"event_id": i})

    events = realtime.get_http_events()
    assert len(events) == 3
    assert events[0]["event_id"] == 0

    # Wait for expiration
    time.sleep(1.1)
    assert realtime.get_http_events() == []


def test_server_worker_update_and_get(realtime):
    agent_id = "test-host"
    worker_id = "worker1"
    worker_data = {"pid": 12345}

    realtime.update("server", {
        "agent_id": agent_id,
        "workers": {
            worker_id: worker_data
        }
    })

    state = realtime.get_server_workers(agent_id)
    assert "master" in state
    assert "workers" in state
    assert worker_id in state["workers"]
    assert state["workers"][worker_id]["pid"] == 12345


def test_update_master_info(realtime):
    agent_id = "test-host"
    master_info = {"pid": 99999}

    realtime.update("server", {
        "agent_id": agent_id,
        "master": master_info
    })

    state = realtime.get_server_workers(agent_id)
    assert state["master"]["pid"] == 99999


def test_get_all_servers(realtime):
    realtime.update("server", {
        "agent_id": "host1",
        "workers": {"w1": {"pid": 111}}
    })
    realtime.update("server", {
        "agent_id": "host2",
        "workers": {"w2": {"pid": 222}},
        "master": {"pid": 999}
    })

    all_servers = realtime.get_all_servers()
    assert "host1" in all_servers
    assert "host2" in all_servers
    assert all_servers["host2"]["master"]["pid"] == 999
    assert all_servers["host1"]["workers"]["w1"]["pid"] == 111


def test_elect_leaders_round_robin(realtime):
    agent_id = "round-host"
    realtime.update("server", {
        "agent_id": agent_id,
        "workers": {
            "w1": {"pid": 1},
            "w2": {"pid": 2},
            "w3": {"pid": 3}
        }
    })

    # Should rotate leader across workers
    leaders = [realtime.elect_leaders()[0]["leader"] for _ in range(6)]
    assert leaders == [3, 1, 2, 3, 1, 2]


def test_dict_output(realtime):
    realtime.update("http", {"type": "GET", "path": "/test"})
    realtime.update("server", {
        "agent_id": "dhost",
        "workers": {
            "w1": {"pid": 123}
        }
    })

    state = realtime.dict()
    assert "http" in state
    assert "server" in state
    assert isinstance(state["http"], list)
    assert "dhost" in state["server"]
    assert "w1" in state["server"]["dhost"]["workers"]
