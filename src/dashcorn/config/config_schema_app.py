from pydantic import BaseModel

class AppConfig(BaseModel):
    default_python_path: str = "src"
    restart_on_crash: bool = True
