from dashcorn.agent.master_reporter import DashcornAgentRunner
from dashcorn.utils.process import run_in_master_only, run_once_per_app

agent = DashcornAgentRunner()

@run_in_master_only()
@run_once_per_app
def start_dashcorn_agent():
    agent.start()

@run_in_master_only()
@run_once_per_app
def stop_dashcorn_agent():
    agent.stop()
