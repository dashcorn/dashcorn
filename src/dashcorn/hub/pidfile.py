import os

from pathlib import Path

PID_FILE = Path.home() / ".config" / "dashcorn" / "hub.pid"

def is_hub_running() -> bool:
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text())
        os.kill(pid, 0)  # kiểm tra tiến trình còn sống
        return True
    except Exception:
        return False

def read_pid():
    return PID_FILE.read_text()

def write_pid():
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))

def clear_pid():
    try:
        PID_FILE.unlink()
    except FileNotFoundError:
        pass
