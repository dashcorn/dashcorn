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
    launcher.start(name, app_path,
        app_object=app_object,
        python_path=python_path,
        host=host,
        port=port,
        workers=workers,
        cwd=cwd)

@sub_cmd.command("stop")
def stop(name: str):
    """Stop the application by name."""
    launcher.stop(name)

@sub_cmd.command("restart")
def restart(name: str):
    """Restart the application."""
    launcher.restart(name)

@sub_cmd.command("list")
def list_apps():
    """List all managed processes."""
    launcher.list()

@sub_cmd.command("delete")
def delete(name: str):
    """Remove the application from the managed list."""
    launcher.delete(name)
