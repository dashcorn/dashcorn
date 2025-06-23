"""
worker_inspector

This module provides utilities for inspecting the current Python process and its
Uvicorn or Gunicorn worker subprocesses. It is designed for environments where
applications are served using Gunicorn with Uvicorn workers (such as FastAPI apps)
and enables basic process-level monitoring and metrics collection.

Main functionalities:
- Gather runtime information about the current process.
- Detect and collect metrics from subprocesses running Uvicorn or Gunicorn.
- Aggregate a summary of all relevant worker metrics for monitoring purposes.

Functions:
    - get_self_process_info() -> Dict:
        Returns detailed process metrics for the current (master) process.

    - find_uvicorn_workers(master_pid: int = None) -> List[Dict]:
        Detects Uvicorn or Gunicorn worker subprocesses spawned by the given master PID.

    - get_all_worker_metrics() -> Dict:
        Returns a summary including the master process info and its active Uvicorn workers.

Dependencies:
    - psutil: Used for process inspection and metric collection.
    - os: For retrieving the current process ID.

Example usage:
    >>> from worker_inspector import get_all_worker_metrics
    >>> metrics = get_all_worker_metrics()
    >>> print(metrics["num_workers"])
    4

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

def get_worker_metrics(leader: Optional[int] = None, include_master: bool = True) -> dict:
    worker = get_self_process_info()
    pid = worker.get("pid")
    master_pid = worker.get("parent_pid")
    if include_master and master_pid and leader == pid:
        master = get_process_info_of(master_pid)
    else:
        master = {}
    return {
        "master": master,
        "workers": {
            str(pid): worker
        }
    }

def find_uvicorn_workers(master_pid: int = None) -> List[Dict]:
    """
    Detect Uvicorn or Gunicorn worker subprocesses spawned by a master process.

    This function searches for child processes of a given master process (typically
    the current Gunicorn master) that appear to be running Uvicorn or Gunicorn workers,
    based on their command-line arguments. It collects key metrics from each matched
    worker process.

    Args:
        master_pid (int, optional): The PID of the master process to inspect.
            If not provided, defaults to the current process's PID.

    Returns:
        List[Dict]: A list of dictionaries, each representing a detected Uvicorn or
        Gunicorn worker subprocess. Each dictionary includes:
            - 'pid': Process ID.
            - 'cpu': CPU usage percentage over a short interval.
            - 'memory': Memory usage in bytes (RSS).
            - 'status': Current process status (e.g., 'running', 'sleeping').
            - 'start_time': UNIX timestamp of when the process started.
            - 'threads': Number of threads used by the process.
            - 'cmdline': The full command-line string used to start the process.

    Notes:
        - Processes that are no longer alive or inaccessible due to permissions
          are safely ignored.
        - CPU usage is measured over a brief interval (0.1 seconds).
    """
    if master_pid is None:
        master_pid = os.getpid()

    master_proc = psutil.Process(master_pid)
    worker_list = []

    try:
        children = master_proc.children(recursive=True)
        for child in children:
            try:
                cmd = " ".join(child.cmdline())
                if "uvicorn" in cmd or "gunicorn" in cmd:
                    worker_list.append({
                        "pid": child.pid,
                        "cpu": child.cpu_percent(interval=0.1),
                        "memory": child.memory_info().rss,
                        "status": child.status(),
                        "start_time": child.create_time(),
                        "threads": child.num_threads(),
                        "cmdline": cmd,
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except psutil.NoSuchProcess:
        pass

    return worker_list

def get_all_worker_metrics() -> Dict:
    """
    Collect metrics for the current (master) process and its Uvicorn worker subprocesses.

    This function retrieves process information for the current process (assumed to be 
    the master Gunicorn process) and identifies any child processes that are Uvicorn 
    workers or subprocesses forked from Uvicorn.

    Returns:
        Dict: A dictionary containing:
            - 'master': A dictionary with metrics about the master process (see `get_self_process_info`).
            - 'workers': A list of dictionaries, each representing metrics for a Uvicorn worker process.
            - 'num_workers': The number of Uvicorn worker processes detected.
    """
    master = get_self_process_info()
    workers = find_uvicorn_workers(master["pid"])
    return {
        "master": master,
        "workers": workers,
    }
