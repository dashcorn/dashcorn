import typer
import os
import subprocess
import yaml

from pathlib import Path
from rich import print

from dashcorn.config.config_loader import DashcornConfig, CONFIG_PATH

config_app = typer.Typer()

@config_app.command("init")
def init(force: bool = typer.Option(False, "--force", "-f", help="Overwrite if config file already exists")):
    """Generate default configuration file from template."""
    if CONFIG_PATH.exists() and not force:
        print(f"[red]Configuration file already exists at {CONFIG_PATH}[/red]")
        print("[yellow]Use --force to overwrite.[/yellow]")
        raise typer.Exit(1)

    cfg = DashcornConfig.default()
    cfg.save()
    print(f"[green]Created configuration file at {CONFIG_PATH}[/green]")

@config_app.command("show")
def show():
    """Display the current configuration."""
    cfg = DashcornConfig.load()
    print(cfg.model_dump_json(indent=2))

@config_app.command("get")
def get_value(section: str, key: str):
    """Get a specific value from the config."""
    cfg = DashcornConfig.load()
    section_obj = getattr(cfg, section, None)
    if section_obj is None:
        print(f"[red]Section '{section}' not found[/red]")
        raise typer.Exit(code=1)
    value = getattr(section_obj, key, None)
    if value is None:
        print(f"[red]Key '{key}' not found in section '{section}'[/red]")
        raise typer.Exit(code=1)
    print(f"[cyan]{section}.{key}[/cyan] = [green]{value}[/green]")

@config_app.command("set")
def set_value(section: str, key: str, value: str):
    """Set a configuration value, with automatic type casting based on schema."""
    cfg = DashcornConfig.load()
    section_obj = getattr(cfg, section, None)
    if section_obj is None:
        print(f"[red]Section '{section}' not found[/red]")
        raise typer.Exit(code=1)

    if not hasattr(section_obj, key):
        print(f"[red]Key '{key}' not found in section '{section}'[/red]")
        raise typer.Exit(code=1)

    old_type = type(getattr(section_obj, key))
    new_value = parse_value(value, old_type)
    setattr(section_obj, key, new_value)
    cfg.save()
    print(f"[green]Updated {section}.{key} = {new_value} ({old_type.__name__})[/green]")

@config_app.command("edit")
def edit():
    """Open the config file using your default editor ($EDITOR)."""
    editor = os.environ.get("EDITOR", "nano")  # fallback if $EDITOR is not set
    subprocess.call([editor, str(CONFIG_PATH)])

@config_app.command("reset")
def reset():
    """Reset configuration to default."""
    confirm = typer.confirm("Are you sure you want to reset the configuration to default?")
    if not confirm:
        raise typer.Exit()

    cfg = DashcornConfig.default()
    cfg.save()
    print("[green]Configuration has been reset to default.[/green]")

@config_app.command("diff")
def diff():
    """Compare current config with default values."""
    from rich.console import Console
    from rich.table import Table

    current = DashcornConfig.load().model_dump()
    default = DashcornConfig.default().model_dump()
    
    def flatten(d, parent_key='', sep='.'):
        """Flatten nested dictionaries to dot notation."""
        items = {}
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(flatten(v, new_key, sep=sep))
            else:
                items[new_key] = v
        return items

    flat_current = flatten(current)
    flat_default = flatten(default)

    all_keys = set(flat_current.keys()) | set(flat_default.keys())

    table = Table(title="Dashcorn Config Diff", show_header=True, header_style="bold magenta")
    table.add_column("Key")
    table.add_column("Default")
    table.add_column("Current", style="yellow")

    differences = 0
    for key in sorted(all_keys):
        val_def = flat_default.get(key, "[red]<missing>[/red]")
        val_cur = flat_current.get(key, "[red]<missing>[/red]")
        if val_def != val_cur:
            table.add_row(key, str(val_def), str(val_cur))
            differences += 1

    if differences:
        console = Console()
        console.print(table)
    else:
        print("[green]No differences from default config.[/green]")

@config_app.command("import")
def import_config(file: Path):
    """Import configuration from a YAML file (overwrite existing config)."""
    if not file.exists():
        print(f"[red]File does not exist: {file}[/red]")
        raise typer.Exit(1)

    try:
        data = yaml.safe_load(file.read_text())
        cfg = DashcornConfig(**data)
        cfg.save()
        print(f"[green]Configuration imported from {file}[/green]")
    except Exception as e:
        print(f"[red]Failed to import configuration:[/red] {e}")
        raise typer.Exit(1)

@config_app.command("export")
def export_config(file: Path):
    """Export current configuration to a YAML file."""
    cfg = DashcornConfig.load()
    content = yaml.safe_dump(cfg.model_dump())
    file.write_text(content)
    print(f"[green]Configuration exported to {file}[/green]")

def parse_value(value: str, expected_type: type):
    """Cast the string value to the appropriate type based on the schema."""
    try:
        if expected_type == bool:
            return value.lower() in ("true", "1", "yes", "on")
        elif expected_type == int:
            return int(value)
        elif expected_type == float:
            return float(value)
        else:
            return value
    except ValueError:
        print(f"[red]Invalid value for type {expected_type.__name__}[/red]")
        raise typer.Exit(code=1)
