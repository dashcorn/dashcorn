DEFAULT_INJECT_CONFIG = {
    "middleware": {
        "lines": [
            "<name_of_app>.add_middleware(MetricsMiddleware)",
        ],
        "imports": [
            "from dashcorn.agent.middleware import MetricsMiddleware",
        ],
    },
    "lifecycle": {
        "on_startup": ["start_dashcorn_agent"],
        "on_shutdown": ["stop_dashcorn_agent"],
        "imports": [
            "from dashcorn.agent.bootstrap import start_dashcorn_agent, stop_dashcorn_agent",
        ],
    },
}
