import yaml

from pathlib import Path
from pydantic import BaseModel

from dashcorn.config.config_schema_app import AppConfig
from dashcorn.config.config_schema_hub import HubConfig

CONFIG_PATH = Path.home() / ".config" / "dashcorn" / "config.yaml"

class DashcornConfig(BaseModel):
    app: AppConfig = AppConfig()
    hub: HubConfig = HubConfig()

    @classmethod
    def exists(cls):
        return CONFIG_PATH.exists()

    @classmethod
    def load(cls):
        if CONFIG_PATH.exists():
            data = yaml.safe_load(CONFIG_PATH.read_text())
            return cls(**data)
        return cls.default()

    @classmethod
    def default(cls):
        return cls(app=AppConfig(), hub=HubConfig())

    def save(self):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        content = yaml.safe_dump(self.model_dump(), sort_keys=False)
        CONFIG_PATH.write_text(content)
