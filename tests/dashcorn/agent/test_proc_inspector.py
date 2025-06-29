import pytest
import os
from unittest.mock import patch, MagicMock

import dashcorn.agent.proc_inspector as inspector


def test_extract_process_info_fields():
    mock_proc = MagicMock()
    mock_proc.pid = 1234
    mock_proc.ppid.return_value = 1000
    mock_proc.name.return_value = "python"
    mock_proc.cmdline.return_value = ["python", "app.py"]
    mock_proc.cpu_percent.return_value = 12.5
    mock_proc.memory_info.return_value = MagicMock(rss=2048000)
    mock_proc.create_time.return_value = 1620000000.0
    mock_proc.num_threads.return_value = 5

    info = inspector.extract_process_info(mock_proc)

    assert info["pid"] == 1234
    assert info["parent_pid"] == 1000
    assert info["name"] == "python"
    assert info["cmdline"] == ["python", "app.py"]
    assert info["cpu"] == 12.5
    assert info["memory"] == 2048000
    assert info["start_time"] == 1620000000.0
    assert info["num_threads"] == 5


@patch("dashcorn.agent.proc_inspector.psutil.Process")
def test_get_process_info_of(mock_psutil_process):
    mock_proc = MagicMock()
    mock_proc.pid = 9999
    mock_proc.ppid.return_value = 123
    mock_proc.name.return_value = "uvicorn"
    mock_proc.cmdline.return_value = ["uvicorn", "app:app"]
    mock_proc.cpu_percent.return_value = 3.0
    mock_proc.memory_info.return_value = MagicMock(rss=4096000)
    mock_proc.create_time.return_value = 1640000000.0
    mock_proc.num_threads.return_value = 4

    mock_psutil_process.return_value = mock_proc

    result = inspector.get_process_info_of(9999)

    assert result["pid"] == 9999
    assert result["cpu"] == 3.0
    assert result["memory"] == 4096000
    assert result["num_threads"] == 4


@patch("dashcorn.agent.proc_inspector.os.getpid", return_value=999)
@patch("dashcorn.agent.proc_inspector.get_process_info_of")
def test_get_self_process_info(mock_get_proc_info, mock_getpid):
    mock_get_proc_info.return_value = {"pid": 999, "cpu": 5.0}
    result = inspector.get_self_process_info()
    assert result["pid"] == 999
    assert result["cpu"] == 5.0
    mock_get_proc_info.assert_called_with(999)


@patch("dashcorn.agent.proc_inspector.get_self_process_info")
@patch("dashcorn.agent.proc_inspector.get_process_info_of")
def test_get_worker_metrics_includes_master(mock_get_master, mock_get_worker):
    # Simulate current worker info
    mock_get_worker.return_value = {
        "pid": 1234,
        "parent_pid": 1000,
        "cpu": 10.0
    }

    # Simulate master info
    mock_get_master.return_value = {
        "pid": 1000,
        "cpu": 1.5
    }

    result = inspector.get_worker_metrics(leader=1234, include_master=True)

    assert result["master"]["pid"] == 1000
    assert result["workers"]["1234"]["cpu"] == 10.0


@patch("dashcorn.agent.proc_inspector.get_self_process_info")
@patch("dashcorn.agent.proc_inspector.get_process_info_of")
def test_get_worker_metrics_excludes_master(mock_get_master, mock_get_worker):
    # Simulate worker not being leader
    mock_get_master.return_value = {}
    mock_get_worker.return_value = {
        "pid": 1234,
        "parent_pid": 1000,
        "cpu": 10.0
    }

    result = inspector.get_worker_metrics(leader=9999, include_master=True)
    assert result["master"] == {}
    assert "1234" in result["workers"]
