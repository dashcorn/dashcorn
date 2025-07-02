import os
from dataclasses import dataclass, asdict, field
from typing import Optional

from dashcorn.commons import consts

@dataclass
class DashboardConfig:
    zmq_pub_control_protocol: str = field(default_factory=lambda:
        os.getenv("DASHCORN_ZMQ_PUB_CONTROL_PROTOCOL", "tcp"))
    zmq_pub_control_address: str = field(default_factory=lambda:
        os.getenv("DASHCORN_ZMQ_PUB_CONTROL_ADDRESS", f"*:{consts.ZMQ_CONNECTION_CONTROL_PORT}"))
    zmq_pull_metrics_protocol: str = field(default_factory=lambda:
        os.getenv("DASHCORN_ZMQ_PULL_METRICS_PROTOCOL", "tcp"))
    zmq_pull_metrics_address: str = field(default_factory=lambda:
        os.getenv("DASHCORN_ZMQ_PULL_METRICS_ADDRESS", f"*:{consts.ZMQ_CONNECTION_METRICS_PORT}"))
    use_curve_auth: bool = field(default_factory=lambda:
        os.getenv("DASHCORN_USE_CURVE", "false").lower() == "true")
    cert_dir: Optional[str] = field(default_factory=lambda:
        os.getenv("DASHCORN_CERT_DIR"))
    leader_rotation_interval: float = field(default_factory=lambda:
        float(os.getenv("DASHCORN_LEADER_ROTATE_INTERVAL", "5.0")))
    enable_logging: bool = field(default_factory=lambda:
        os.getenv("DASHCORN_ENABLE_LOGGING", "false").lower() == "true")

    @property
    def zmq_pub_control_endpoint(self) -> str:
        return f"{self.zmq_pub_control_protocol}://{self.zmq_pub_control_address}"

    @property
    def zmq_pull_metrics_endpoint(self) -> str:
        return f"{self.zmq_pull_metrics_protocol}://{self.zmq_pull_metrics_address}"

    def to_dict(self) -> dict:
        return asdict(self)

    def __repr__(self) -> str:
        return (
            f"<DashboardConfig "
            f"zmq_pub_control_endpoint={self.zmq_pub_control_endpoint} "
            f"zmq_pull_metrics_endpoint={self.zmq_pull_metrics_endpoint} "
            f"use_curve_auth={self.use_curve_auth}>"
        )
