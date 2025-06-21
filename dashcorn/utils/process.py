import os
import functools
import logging
import threading
import psutil

logger = logging.getLogger(__name__)

_HAS_RUN_LOCK = threading.Lock()
_HAS_RUN_FLAGS = {}

def run_in_master_only(use_children_check: bool = False):
    """
    Decorator: Run the function only if NOT inside a Uvicorn worker process.
    Optionally, use psutil to check if process has children (i.e. master).

    Args:
        use_children_check (bool): Whether to check if current process has child workers
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Case 1: Uvicorn sets UVICORN_WORKER=true for worker processes
            current_proc = psutil.Process()
            logger.debug(f"parent: { current_proc.ppid() }")
            logger.debug(f"🏁 [{func.__name__}] UVICORN_WORKER={ os.getenv("UVICORN_WORKER") }.")
            if os.getenv("UVICORN_WORKER") == "true":
                logger.debug(f"⛔ Skipping {func.__name__} — running in worker (env var).")
                return None

            # Case 2: Optionally check child processes
            if use_children_check:
                try:
                    proc = psutil.Process()
                    children = proc.children()
                    if len(children) == 0:
                        logger.debug(f"⛔ Skipping {func.__name__} — no child processes detected.")
                        return None
                    logger.debug(f"✅ Found {len(children)} child process(es).")
                except Exception as e:
                    logger.warning(f"⚠️ Could not check children for {func.__name__}: {e}")

            logger.debug(f"✅ Running {func.__name__} in master process.")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def run_once_per_app(func):
    """
    Decorator: Run this function only once per application lifetime.
    Useful when same logic may be called from multiple places.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with _HAS_RUN_LOCK:
            if _HAS_RUN_FLAGS.get(func.__name__):
                logger.debug(f"⏩ Skipping {func.__name__} — already executed.")
                return None
            logger.debug(f"🏁 First execution of {func.__name__}.")
            _HAS_RUN_FLAGS[func.__name__] = True
        return func(*args, **kwargs)
    return wrapper
