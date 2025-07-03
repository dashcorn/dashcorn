import typer
import subprocess

from rich import print

from dashcorn.config.config_loader import DashcornConfig

hub_app = typer.Typer()

@hub_app.command("run")
def start(
    host: str = typer.Option(None, help="Host to bind Dashcorn Hub"),
    port: int = typer.Option(None, help="Port to bind Dashcorn Hub")
):
    """Run the Dashcorn Hub using configured host and port by default."""

    cfg = DashcornConfig.load()

    # Use config as fallback if CLI not specified
    actual_host = host or cfg.hub.server_host
    actual_port = port or cfg.hub.server_port

    print(f"[cyan]Starting Dashcorn Hub at http://{actual_host}:{actual_port}[/cyan]")

    subprocess.run([
            "uvicorn",
            "dashcorn.hub.server:app",
            "--host", actual_host,
            "--port", str(actual_port),
            "--reload"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

@hub_app.command()
def status():
    """Display current status (placeholder)"""
    typer.echo("📊 Dashcorn status (demo):")
    typer.echo(" - Dashboard running: Unknown (check port 5555)")
    typer.echo(" - Agent data sent: Use `/metrics` endpoint to verify")
