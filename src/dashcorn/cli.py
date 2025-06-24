import typer
import subprocess
import httpx
import os
from datetime import datetime
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
    typer.echo(" - Dashboard running: Unknown (check port 5555)")
    typer.echo(" - Agent data sent: Use `/metrics` endpoint to verify")

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

@app.command()
def show(kind: str = typer.Argument(..., help="master or workers")):
    """
    Show master or workers status from Dashcorn dashboard
    """
    try:
        res = httpx.get("http://localhost:5555/metrics")
        data = res.json()
    except Exception as e:
        typer.echo(f"❌ Failed to connect to dashboard: {e}")
        raise typer.Exit(1)

    for host, info in data.get("server", {}).items():
        typer.echo(f"\nHost: {host}")
        if kind == "master":
            master = info.get("master", {})
            if not master:
                continue
            typer.echo(f"  PID: {master.get('pid')}")
            typer.echo(f"  CPU: {master.get('cpu')}%")
            typer.echo(f"  RAM: {master.get('memory', 0) / 1024 / 1024:.2f} MB")
            typer.echo(f"  Threads: {master.get('num_threads')}")
            start_time = master.get("start_time", 0)
            if start_time:
                uptime = datetime.now().timestamp() - start_time
                typer.echo(f"  Uptime: {uptime:.1f} seconds")
        elif kind == "workers":
            workers = info.get("workers", [])
            typer.echo(f"  Total workers: {len(workers)}")
            for _, w in workers.items():
                typer.echo(f"    - PID: {w.get('pid')}, CPU: {w.get('cpu')}%, RAM: {w.get('memory') / 1024 / 1024:.1f} MB")
        else:
            typer.echo(f"⚠️ Unknown type: {kind}. Use 'master' or 'workers'.")

if __name__ == "__main__":
    app()
