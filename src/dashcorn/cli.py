import typer
import httpx

from datetime import datetime
from pathlib import Path

app = typer.Typer(help="Dashcorn – A real-time dashboard for FastAPI/Uvicorn applications")

from dashcorn.cli_app import sub_cmd as scmd_app
app.add_typer(scmd_app, name="app", help="Dashcorn Application launcher")

from dashcorn.cli_config import config_app
app.add_typer(config_app, name="config", help="Dashcorn Config management")

from dashcorn.cli_hub import hub_app
app.add_typer(hub_app, name="hub", help="Dashcorn Hub management")

from dashcorn.cli_agent import sub_cmd as scmd_agent
app.add_typer(scmd_agent, name="agent", help="Set of commands related to agents")

from dashcorn.cli_hook import sub_cmd as cli_hook
app.add_typer(cli_hook, name="hook", help="Automatically insert middleware into app.py")

if __name__ == "__main__":
    app()
