import typer
import subprocess
import os
import yaml

from pathlib import Path

from dashcorn.command.code_hook_injector import (
    DEFAULT_INJECT_CONFIG,
    inject_middlewares_to_source_file,
    inject_lifecycle_to_source_file
)

from dashcorn.command import hook_template_config as hooks

from rich.console import Console
from rich.text import Text

console = Console()

def _load_config_from_template_file(from_template_file: bool):
    if from_template_file:
        config_file = Path.home() / ".config" / "dashcorn" / "hook-template.yaml"
        if not config_file.exists():
            raise FileNotFoundError("Template file not found. Run: dashcorn inject save-template-file")
        with config_file.open("r", encoding="utf-8") as f:
            inject_config = yaml.safe_load(f)
    else:
        inject_config = DEFAULT_INJECT_CONFIG
    return inject_config

sub_cmd = typer.Typer()

@sub_cmd.command("all")
def inject_all_cmd(
    file: Path,
    from_template_file: bool = typer.Option(False, help="Use YAML template from ~/.config/dashcorn/hook-template.yaml"),
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


@sub_cmd.command("middleware")
def inject_middleware_cmd(
    file: Path,
    from_template_file: bool = typer.Option(False, help="Use YAML template from ~/.config/dashcorn/hook-template.yaml"),
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


@sub_cmd.command("lifecycle")
def inject_lifecycle_cmd(
    file: Path,
    from_template_file: bool = typer.Option(False, help="Use YAML template from ~/.config/dashcorn/hook-template.yaml"),
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


@sub_cmd.command("init-template-file")
def init_template_file():
    """
    Initialize hook-template.yaml with the default template.
    Will not overwrite if the file already exists.
    """
    created = hooks.init_hook_template()
    config_path = hooks.get_hook_config_path()

    if created:
        typer.echo(f"✅ Template initialized at: {config_path}")
    else:
        typer.echo(f"⚠️ Config already exists at: {config_path}")


@sub_cmd.command("reset-template-file")
def reset_template_file():
    """
    Overwrite hook-template.yaml with the default template.
    WARNING: This will erase existing customizations.
    """
    hooks.reset_hook_template()
    typer.echo(f"♻️ Template has been reset at: {hooks.get_hook_config_path()}")


@sub_cmd.command("edit-template-file")
def edit_template_file():
    """
    Open the hook-template.yaml template in $EDITOR for manual editing.
    If the file does not exist, it will be created using the default template.
    """
    config_path = hooks.get_hook_config_path()
    created = hooks.init_hook_template()
    if created:
        typer.echo(f"📄 Created new config at {config_path}")

    editor = os.getenv("EDITOR") or ("notepad" if os.name == "nt" else "nano")
    try:
        typer.echo(f"📝 Opening {config_path} with editor: {editor}")
        subprocess.run([editor, str(config_path)])
    except FileNotFoundError:
        typer.echo(f"❌ Editor '{editor}' not found. Please set your $EDITOR environment variable.", err=True)
        raise typer.Exit(1)


@sub_cmd.command("view-template-file")
def view_template_file():
    """
    Print the contents of the hook-template.yaml template to the terminal.
    If the file does not exist, it will be created using the default template.
    """
    content = hooks.read_hook_template()
    typer.echo(f"📂 Config path: {hooks.get_hook_config_path()}")
    typer.echo("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    typer.echo(content.strip())
    typer.echo("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


@sub_cmd.command("diff-template-file")
def diff_template_file(plain: bool = typer.Option(False, "--plain", "--no-color", help="Output plain text without colors.")):
    """
    Show the difference between hook-template.yaml and the default template (with optional colors).
    """
    diff_lines = hooks.diff_hook_template()
    if not diff_lines:
        msg = "✅ Your hook-template.yaml is identical to the default."
        if plain:
            typer.echo(msg)
        else:
            console.print(f"[bold green]{msg}[/]")
        return

    if plain:
        typer.echo("🔍 Differences between current config and default:")
        typer.echo("\n".join(diff_lines))
    else:
        console.print("🔍 [bold yellow]Differences between current config and default:[/]")
        for line in diff_lines:
            if line.startswith("+") and not line.startswith("+++"):
                console.print(Text(line, style="green"))
            elif line.startswith("-") and not line.startswith("---"):
                console.print(Text(line, style="red"))
            elif line.startswith("@@"):
                console.print(Text(line, style="blue"))
            elif line.startswith(("---", "+++")):
                console.print(Text(line, style="magenta"))
            else:
                console.print(line)
