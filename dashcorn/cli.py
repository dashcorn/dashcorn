import typer
import subprocess
import os
from pathlib import Path

app = typer.Typer(help="Dashcorn – A real-time dashboard for FastAPI/Uvicorn applications")

@app.command()
def dashboard(
    host: str = "127.0.0.1",
    port: int = 5555,
):
    """Start the Dashcorn dashboard"""
    typer.echo(f"🔌 Starting Dashcorn dashboard at http://{host}:{port} ...")
    subprocess.run(["uvicorn", "dashcorn.dashboard.main:app", "--host", host, "--port", str(port)])

@app.command()
def status():
    """Display current status (placeholder)"""
    typer.echo("📊 Dashcorn status (demo):")
    typer.echo("- Dashboard running: Unknown (check port 5555)")
    typer.echo("- Agent data sent: Use `/metrics` endpoint to verify")
    # Can be extended to read ZMQ socket or query endpoint in the future

@app.command()
def install():
    """(Optional) Automatically insert Dashcorn middleware into app.py"""
    app_file = Path("app.py")
    if app_file.exists():
        content = app_file.read_text()
        if "from dashcorn.agent.middleware" in content:
            typer.echo("✅ Middleware already added.")
        else:
            insert = "from dashcorn.agent.middleware import MetricsMiddleware\napp.add_middleware(MetricsMiddleware)\n"
            content = content.replace("app = FastAPI()", "app = FastAPI()\n" + insert)
            app_file.write_text(content)
            typer.echo("✅ MetricsMiddleware successfully added to app.py.")
    else:
        typer.echo("⚠️ Could not find app.py to insert middleware.")

if __name__ == "__main__":
    app()
