import os
import signal
import logging
import typer
import subprocess
import sys

from rich import print

from .pidfile import is_hub_running, read_pid

logger = logging.Logger(__name__)

app = typer.Typer(add_completion=False)

@app.command("run")
def run():
    if is_hub_running():
        print("[dashcorn] Hub daemon is already running.")
        raise typer.Exit()

    proc = subprocess.Popen(
        [ sys.executable, "-m", "dashcorn.hub.daemon" ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    print(f"[dashcorn] Starting hub daemon process... (PID: {proc.pid})")


@app.command("stop")
def stop():
    """
    Terminate the running Dashcorn Hub service by sending SIGTERM.
    """
    if not is_hub_running():
        print("[dashcorn] No running Hub service found.")
        raise typer.Exit(code=1)

    try:
        pid = int(read_pid())
        os.kill(pid, signal.SIGTERM)
        print(f"[dashcorn] Sent SIGTERM to Hub process (PID: {pid}).")
    except Exception as e:
        print(f"[dashcorn] Failed to terminate Hub service: {e}")
        raise typer.Exit(code=1)
