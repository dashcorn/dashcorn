from pydantic import BaseModel

from dashcorn.commons import consts

class HubConfig(BaseModel):
    server_host: str = "127.0.0.1"
    server_port: int = 5555
    pub_control_address: str = f"*:{consts.ZMQ_CONNECTION_CONTROL_PORT}"
    pub_control_protocol: str = "tcp"
    pull_metrics_address: str = f"*:{consts.ZMQ_CONNECTION_METRICS_PORT}"
    pull_metrics_protocol: str = "tcp"
    prom_exporter_enabled: bool = True
    prom_exporter_port: int = 9200
