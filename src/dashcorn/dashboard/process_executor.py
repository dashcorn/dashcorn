import subprocess, os, json, signal, time, threading, psutil, sys

from pathlib import Path
from typing import Optional

PM_FILE = Path.home() / ".config" / "dashcorn" / "running.json"
PM_FILE.parent.mkdir(parents=True, exist_ok=True)

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
        if name in self.processes:
            print(f"[dashcorn] Process '{name}' already exists.")
            return

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

        print(f"[dashcorn] Starting process '{name}'...")
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

    def stop(self, name):
        if name not in self.processes:
            print(f"[dashcorn] Process '{name}' not found.")
            return
        pid = self.processes[name]["pid"]
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"[dashcorn] Stopped process '{name}' (PID: {pid})")
        except ProcessLookupError:
            print(f"[dashcorn] Process '{name}' already stopped.")
        self.processes.pop(name)
        self.save()

    def restart(self, name):
        if name not in self.processes:
            print(f"[dashcorn] Process '{name}' not found.")
            return
        app_path = self.processes[name]["app_path"]
        self.stop(name)
        time.sleep(1)
        self.start(name, app_path)

    def list(self):
        print(f"{'Name':<15}{'PID':<8}{'Status':<10}{'App Path'}")
        print("-" * 60)
        for name, meta in self.processes.items():
            pid = meta["pid"]
            status = "Running" if psutil.pid_exists(pid) else "Crashed"
            print(f"{name:<15}{pid:<8}{status:<10}{meta['app_path']}")

    def delete(self, name):
        self.processes.pop(name, None)
        self.save()
        print(f"[dashcorn] Deleted process '{name}' from list.")
