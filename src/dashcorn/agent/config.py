import os
from dataclasses import dataclass, field, asdict
from typing import Optional

from dashcorn.commons import consts

def env_bool(key: str, default: str = "false") -> bool:
    return os.getenv(key, default).strip().lower() == "true"

def env_float(key: str, default: str = "5.0") -> float:
    try:
        return float(os.getenv(key, default))
    except ValueError:
        return float(default)

@dataclass
class AgentConfig:
    zmq_report_protocol: str = field(default_factory=lambda: os.getenv("DASHCORN_ZMQ_REPORT_PROTOCOL", "tcp"))
    zmq_report_addr: str = field(default_factory=lambda: os.getenv("DASHCORN_ZMQ_REPORT_ADDR",
            f"{consts.ZMQ_CONNECTION_METRICS_HOST}:{consts.ZMQ_CONNECTION_METRICS_PORT}"))
    zmq_control_protocol: str = field(default_factory=lambda: os.getenv("DASHCORN_ZMQ_CONTROL_PROTOCOL", "tcp"))
    zmq_control_addr: str = field(default_factory=lambda: os.getenv("DASHCORN_ZMQ_CONTROL_ADDR",
            f"{consts.ZMQ_CONNECTION_CONTROL_HOST}:{consts.ZMQ_CONNECTION_CONTROL_PORT}"))
    use_curve_auth: bool = field(default_factory=lambda: env_bool("DASHCORN_USE_CURVE", "false"))
    cert_dir: Optional[str] = field(default_factory=lambda: os.getenv("DASHCORN_CERT_DIR"))
    interval_seconds: float = field(default_factory=lambda: env_float("DASHCORN_INTERVAL", "5.0"))
    enable_logging: bool = field(default_factory=lambda: env_bool("DASHCORN_ENABLE_LOGGING", "false"))

    @property
    def zmq_report_endpoint(self) -> str:
        """Returns the full ZMQ endpoint for reporting metrics (PUSH → PULL)."""
        return f"{self.zmq_report_protocol}://{self.zmq_report_addr}"

    @property
    def zmq_control_endpoint(self) -> str:
        """Returns the full ZMQ endpoint for control channel (REP ↔ REQ or PUB → SUB)."""
        return f"{self.zmq_control_protocol}://{self.zmq_control_addr}"

    def to_dict(self) -> dict:
        """
        Return a dictionary representation of the configuration.
        Includes computed properties like zmq endpoints.
        """
        return {
            **asdict(self),
            "zmq_report_endpoint": self.zmq_report_endpoint,
            "zmq_control_endpoint": self.zmq_control_endpoint,
        }

    def __repr__(self) -> str:
        """
        Return a detailed string representation of the config, helpful for debugging.
        """
        return (
            f"<AgentConfig("
            f"zmq_report_endpoint={self.zmq_report_endpoint}, "
            f"zmq_control_endpoint={self.zmq_control_endpoint}, "
            f"use_curve_auth={self.use_curve_auth}, "
            f"interval_seconds={self.interval_seconds}, "
            f"enable_logging={self.enable_logging})>"
        )
