import subprocess, os, json, signal, time, threading, psutil, sys
import logging

from pathlib import Path
from typing import Optional

PM_FILE = Path.home() / ".config" / "dashcorn" / "running.json"
PM_FILE.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

class ProcessExecutor:
    def __init__(self):
        self.load()

    def load(self):
        if PM_FILE.exists():
            with open(PM_FILE, "r") as f:
                self.processes = json.load(f)
        else:
            self.processes = {}

    def save(self):
        with open(PM_FILE, "w") as f:
            json.dump(self.processes, f, indent=2)

    def start(self, name, app_path, app_object: str = "app",
            python_path: Optional[str] = None,
            port: Optional[int] = 7979,
            host: Optional[str] = None,
            workers: Optional[int] = None,
            cwd: Optional[str] = None,
    ):
        result = dict(status="ok")

        if name in self.processes:
            result.update(status="already_exists")
            return result

        env = os.environ.copy()

        if python_path is not None:
            env["PYTHONPATH"] = python_path

        exec_args = [
            sys.executable, "-m", "uvicorn",
            f"{app_path.replace('/', '.').removesuffix('.py')}:{app_object}",
        ]

        if host is not None:
            exec_args += ["--host", host]

        if port is not None:
            exec_args += ["--port", str(port)]

        if workers is not None:
            if workers <= 0:
                return
            if workers >16:
                pass
            exec_args += ["--workers", str(workers)]

        logger.debug(f"[dashcorn] Starting process '{name}'...")
        proc = subprocess.Popen(exec_args,
            env=env,
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.processes[name] = {
            "pid": proc.pid,
            "app_path": app_path,
            "start_time": time.time(),
        }
        self.save()

        result.update(proc=dict(self.processes[name]))
        return result

    def stop(self, name):
        result = dict(status="ok")
        if name not in self.processes:
            result.update(status="not_found")
            return result
        pid = self.processes[name]["pid"]
        result.update(pid=pid)
        try:
            os.kill(pid, signal.SIGTERM)
            result.update(status="ok")
        except ProcessLookupError:
            result.update(status="already_stopped")
        finally:
            self.processes.pop(name)
            self.save()
        return result

    def restart(self, name):
        result = dict(status="ok")
        if name not in self.processes:
            result.update(status="not_found")
            return result
        app_path = self.processes[name]["app_path"]
        self.stop(name)
        time.sleep(1)
        self.start(name, app_path)
        return result

    def list(self):
        result = dict(status="ok")
        procs = []
        for name, meta in self.processes.items():
            pid = meta["pid"]
            if psutil.pid_exists(pid):
                procs.append(dict(name=name, pid=pid, status="running", app_path=meta.get("app_path")))
            else:
                procs.append(dict(name=name, pid=pid, status="crashed", app_path=meta.get("app_path")))
        result.update(processes=procs)
        return result

    def delete(self, name):
        result = dict(status="ok")
        if name not in self.processes:
            result.update(status="not_found")
            return result
        self.processes.pop(name, None)
        self.save()
        return result
