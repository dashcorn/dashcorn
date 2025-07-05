"""
proc_inspector

This module provides utilities for inspecting the current Python process and its
Uvicorn or Gunicorn worker subprocesses. It is designed for environments where
applications are served using Gunicorn with Uvicorn workers (such as FastAPI apps)
and enables basic process-level monitoring and metrics collection.

Main functionalities:
- Gather runtime information about the current process.
- Detect and collect metrics from subprocesses running Uvicorn or Gunicorn.
- Aggregate a summary of all relevant worker metrics for monitoring purposes.

This module is useful for lightweight observability in production Python web services.
"""

import os
import psutil
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

def get_self_process_info() -> Dict:
    """
    Retrieve information about the current running process.

    Returns:
        Dict: A dictionary containing details of the current process, including:
            - 'pid': Process ID.
            - 'cmdline': Command-line arguments used to start the process.
            - 'cpu': CPU usage percentage over a short interval.
            - 'memory': Resident Set Size (RSS) memory usage in bytes.
            - 'start_time': The start time of the process (as a UNIX timestamp).
            - 'num_threads': The number of threads used by the process.
    """
    return get_process_info_of(os.getpid())

def get_process_info_of(pid) -> Dict:
    return extract_process_info(psutil.Process(pid))

def extract_process_info(proc) -> Dict:
    return {
        "pid": proc.pid,
        "parent_pid": proc.ppid(),
        "name": proc.name(),
        "cmdline": proc.cmdline(),
        "cpu": proc.cpu_percent(interval=0.1),
        "memory": proc.memory_info().rss,
        "start_time": proc.create_time(),
        "num_threads": proc.num_threads(),
    }

def get_worker_metrics(leader: Optional[int] = None,
        heartbeat: Optional[int] = None,
        include_master: bool = False) -> dict:
    worker = get_self_process_info()
    pid = worker.get("pid")
    master_pid = worker.get("parent_pid")
    if heartbeat:
        worker.update(heartbeat=heartbeat)

    if master_pid and (include_master or leader == pid):
        master = get_process_info_of(master_pid)
        logger.debug(f"👷 pid: {pid} == leader: {leader} #{heartbeat} -> selected leader: {pid}")
    else:
        master = {}
        logger.debug(f"👷 pid: {pid} <> leader: {leader} #{heartbeat} -x")

    return {
        "master": master,
        "workers": {
            str(pid): worker
        }
    }
