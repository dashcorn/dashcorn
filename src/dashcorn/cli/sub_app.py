import typer
from rich import print

from dashcorn.command.process_launcher import ProcessLauncher

launcher = ProcessLauncher()
sub_cmd = typer.Typer()

@sub_cmd.command("start")
def start(
    name: str,
    app_path: str,
    app_object: str = typer.Option("app", help="Name of app variable (default: app)"),
    python_path: str = typer.Option(None, "--python-path", help="PYTHONPATH environment variable"),
    host: str = typer.Option("127.0.0.1", help="Host to bind app"),
    port: int = typer.Option(None, help="Port to bind app"),
    workers: int = typer.Option(None, help="Number of workers"),
    cwd: str = typer.Option(None, "--working-dir", help="Current working dir"),
):
    """Start an application by name and path."""
    result = launcher.start(name, app_path,
        app_object=app_object,
        python_path=python_path,
        host=host,
        port=port,
        workers=workers,
        cwd=cwd)
    status = result.get("status")

    if status == "already_exists":
        print(f"[dashcorn] Process '{name}' already exists.")
        return result

    if status == "ok":
        pid = result.get("proc", {}).get("pid")
        print(f"[dashcorn] Starting process '{name}' started, pid: {pid}")
        return result

@sub_cmd.command("stop")
def stop(name: str):
    """Stop the application by name."""
    result = launcher.stop(name)
    status = result.get("status")
    if status == "not_found":
        print(f"[dashcorn] Process '{name}' not found.")
        return result
    if status == "already_stopped":
        print(f"[dashcorn] Process '{name}' already stopped.")
        return result
    if status == "ok":
        pid = result.get("pid")
        print(f"[dashcorn] Stopped process '{name}' (PID: {pid})")
        return result

@sub_cmd.command("restart")
def restart(name: str):
    """Restart the application."""
    result = launcher.restart(name)
    status = result.get("status")
    if status == "not_found":
        print(f"[dashcorn] Process '{name}' not found.")
        return result
    print(f"[dashcorn] Process '{name}' restarted.")
    return result

@sub_cmd.command("list")
def list_apps():
    """List all managed processes."""
    result = launcher.list()
    print(f"{'Name':<15}{'PID':<8}{'Status':<10}{'App Path'}")
    print("-" * 60)
    for meta in result.get("processes"):
        name = meta.get("name")
        pid = meta.get("pid")
        status = meta.get("status")
        app_path = meta.get("app_path")
        print(f"{name:<15}{pid:<8}{status:<10}{app_path}")
    return result

@sub_cmd.command("delete")
def delete(name: str):
    """Remove the application from the managed list."""
    result = launcher.delete(name)
    status = result.get("status")
    if status == "not_found":
        print(f"[dashcorn] Process '{name}' not found.")
    elif status == "ok":
        print(f"[dashcorn] Deleted process '{name}' from list.")
    return result
