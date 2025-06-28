import difflib
import typer
import subprocess
import httpx
import os
import yaml

from datetime import datetime
from pathlib import Path

app = typer.Typer(help="Dashcorn – A real-time dashboard for FastAPI/Uvicorn applications")

#--------------------------------------------------------------------------------------------------

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

#--------------------------------------------------------------------------------------------------

from dashcorn.command.code_hook_injector import (
    DEFAULT_INJECT_CONFIG,
    inject_middlewares_to_source_file,
    inject_lifecycle_to_source_file
)

def _load_config_from_template_file(from_template_file: bool):
    if from_template_file:
        config_file = Path.home() / ".config" / "dashcorn" / "hook-config.yml"
        if not config_file.exists():
            raise FileNotFoundError("Template file not found. Run: dashcorn inject save-template-file")
        with config_file.open("r", encoding="utf-8") as f:
            inject_config = yaml.safe_load(f)
    else:
        inject_config = DEFAULT_INJECT_CONFIG
    return inject_config


scmd_inject = typer.Typer()
app.add_typer(scmd_inject, name="inject", help="(Optional) Automatically insert Dashcorn middleware into app.py")


@scmd_inject.command("all")
def inject_all_cmd(
    file: Path,
    from_template_file: bool = typer.Option(False, help="Use YAML template from ~/.config/dashcorn/hook-config.yml"),
    backup: bool = typer.Option(True, help="Create a .bak backup before modifying the source file.")
):
    """
    Inject both middleware and lifecycle hooks into a FastAPI source file.
    """
    try:
        inject_config = _load_config_from_template_file(from_template_file)

        inject_middlewares_to_source_file(str(file), config=inject_config, backup=backup)
        inject_lifecycle_to_source_file(str(file), config=inject_config, backup=False)

        typer.echo(f"✅ Middleware and lifecycle hooks injected into {file}")
    except Exception as e:
        typer.echo(f"❌ Injection failed: {e}", err=True)


@scmd_inject.command("middleware")
def inject_middleware_cmd(
    file: Path,
    from_template_file: bool = typer.Option(False, help="Use YAML template from ~/.config/dashcorn/hook-config.yml"),
    backup: bool = typer.Option(True, help="Create a .bak backup before modifying the source file."),
):
    """
    Inject middleware and import statements into a FastAPI source file.
    """
    try:
        inject_config = _load_config_from_template_file(from_template_file)
        inject_middlewares_to_source_file(str(file), config=inject_config, backup=backup)
        typer.echo(f"✅ Middleware injected into {file}")
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)


@scmd_inject.command("lifecycle")
def inject_lifecycle_cmd(
    file: Path,
    from_template_file: bool = typer.Option(False, help="Use YAML template from ~/.config/dashcorn/hook-config.yml"),
    backup: bool = typer.Option(True, help="Create a .bak backup before modifying the source file."),
):
    """
    Inject startup/shutdown lifecycle hooks into a FastAPI source file.
    """
    try:
        inject_config = _load_config_from_template_file(from_template_file)
        inject_lifecycle_to_source_file(str(file), config=inject_config, backup=backup)
        typer.echo(f"✅ Lifecycle hooks injected into {file}")
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)


@scmd_inject.command("init-template-file")
def init_template_file():
    """
    Initialize hook-config.yml with the default template.
    Will not overwrite if the file already exists.
    """
    config_file = Path.home() / ".config" / "dashcorn" / "hook-config.yml"
    config_file.parent.mkdir(parents=True, exist_ok=True)

    if config_file.exists():
        typer.echo(f"⚠️ Config already exists: {config_file}")
        return

    with config_file.open("w", encoding="utf-8") as f:
        yaml.dump(DEFAULT_INJECT_CONFIG, f, allow_unicode=True)

    typer.echo(f"✅ Template initialized at: {config_file}")


@scmd_inject.command("reset-template-file")
def reset_template_file():
    """
    Overwrite hook-config.yml with the default template.
    WARNING: This will erase existing customizations.
    """
    config_file = Path.home() / ".config" / "dashcorn" / "hook-config.yml"
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with config_file.open("w", encoding="utf-8") as f:
        yaml.dump(DEFAULT_INJECT_CONFIG, f, allow_unicode=True)

    typer.echo(f"♻️ Template has been reset to default at: {config_file}")


@scmd_inject.command("edit-template-file")
def edit_template_file():
    """
    Open the hook-config.yml template in $EDITOR for manual editing.
    If the file does not exist, it will be created using the default template.
    """
    config_file = Path.home() / ".config" / "dashcorn" / "hook-config.yml"
    config_file.parent.mkdir(parents=True, exist_ok=True)

    if not config_file.exists():
        with config_file.open("w", encoding="utf-8") as f:
            yaml.dump(DEFAULT_INJECT_CONFIG, f, allow_unicode=True)
        typer.echo(f"📄 Created default config at {config_file}")

    editor = os.getenv("EDITOR")
    if not editor:
        editor = "notepad" if os.name == "nt" else "nano"

    try:
        typer.echo(f"📝 Opening {config_file} with editor: {editor}")
        subprocess.run([editor, str(config_file)])
    except FileNotFoundError:
        typer.echo(f"❌ Editor '{editor}' not found. Please set your $EDITOR environment variable.", err=True)
        raise typer.Exit(1)


@scmd_inject.command("view-template-file")
def view_template_file():
    """
    Print the contents of the hook-config.yml template to the terminal.
    If the file does not exist, it will be created using the default template.
    """
    config_file = Path.home() / ".config" / "dashcorn" / "hook-config.yml"
    config_file.parent.mkdir(parents=True, exist_ok=True)

    if not config_file.exists():
        with config_file.open("w", encoding="utf-8") as f:
            yaml.dump(DEFAULT_INJECT_CONFIG, f, allow_unicode=True)
        typer.echo(f"📄 Created default config at {config_file}")

    with config_file.open("r", encoding="utf-8") as f:
        content = f.read()

    typer.echo(f"📂 Config path: {config_file}")
    typer.echo("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    typer.echo(content.strip())
    typer.echo("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


@scmd_inject.command("diff-template-file")
def diff_template_file():
    """
    Show the difference between the current hook-config.yml file
    and the DEFAULT_INJECT_CONFIG.
    """
    config_file = Path.home() / ".config" / "dashcorn" / "hook-config.yml"
    config_file.parent.mkdir(parents=True, exist_ok=True)

    if not config_file.exists():
        with config_file.open("w", encoding="utf-8") as f:
            yaml.dump(DEFAULT_INJECT_CONFIG, f, allow_unicode=True)
        typer.echo(f"📄 Created default config at {config_file}")

    # Load actual YAML content from file
    with config_file.open("r", encoding="utf-8") as f:
        actual_yaml = f.read()

    # Convert DEFAULT_INJECT_CONFIG to YAML string
    default_yaml = yaml.dump(DEFAULT_INJECT_CONFIG, allow_unicode=True)

    # Compare line-by-line
    diff = difflib.unified_diff(
        default_yaml.splitlines(),
        actual_yaml.splitlines(),
        fromfile="DEFAULT_INJECT_CONFIG",
        tofile=str(config_file),
        lineterm=""
    )

    diff_output = list(diff)
    if diff_output:
        typer.echo("🔍 Differences between current config and default:")
        typer.echo("\n".join(diff_output))
    else:
        typer.echo("✅ Your hook-config.yml is identical to the default.")

#--------------------------------------------------------------------------------------------------

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
