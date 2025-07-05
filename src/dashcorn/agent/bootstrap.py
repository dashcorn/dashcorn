import threading

from typing import Optional

from .config import AgentConfig
from .worker_sender import MetricsSender
from .settings_store import SettingsStore
from .settings_listener import SettingsListener
from .worker_reporter import WorkerReporter

_settings_store: Optional[SettingsStore] = None
_settings_listener: Optional[SettingsListener] = None
_metrics_sender: Optional[MetricsSender] = None
_worker_reporter: Optional[WorkerReporter] = None

_bootstrap_lock = threading.Lock()


def start_dashcorn_agent(config: Optional[AgentConfig] = None):
    with _bootstrap_lock:
        return _start_dashcorn_agent_in_safe(config)

def _start_dashcorn_agent_in_safe(config: Optional[AgentConfig] = None):
    _config = config or AgentConfig()

    global _settings_store
    if _settings_store is None:
        _settings_store = SettingsStore()

    global _settings_listener
    if _settings_listener is None:
        _settings_listener = SettingsListener(
                address=_config.zmq_control_address,
                protocol=_config.zmq_control_protocol,
                handle_message=_settings_store.update_settings)
        _settings_listener.start()

    global _metrics_sender
    if _metrics_sender is None:
        _metrics_sender = MetricsSender(
                address=_config.zmq_metrics_address,
                protocol=_config.zmq_metrics_protocol,
                logging_enabled=_config.enable_logging)

    global _worker_reporter
    if _worker_reporter is None:
        _worker_reporter = WorkerReporter(interval=4.0,
            settings_store=_settings_store,
            metrics_sender=_metrics_sender)
        _worker_reporter.start()

    return dict(metrics_sender=_metrics_sender)


def stop_dashcorn_agent():
    with _bootstrap_lock:
        _stop_dashcorn_agent_in_safe()

def _stop_dashcorn_agent_in_safe():
    global _settings_listener
    if _settings_listener:
        _settings_listener.stop()
        _settings_listener = None

    global _worker_reporter
    if _worker_reporter:
        _worker_reporter.stop()
        _worker_reporter = None

    global _metrics_sender
    if _metrics_sender:
        _metrics_sender.close()
        _metrics_sender = None
