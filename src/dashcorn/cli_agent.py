import typer
import httpx

from datetime import datetime

sub_cmd = typer.Typer()

@sub_cmd.command("show")
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
