from pathlib import Path
import yaml
import difflib

from .code_hook_injector import DEFAULT_INJECT_CONFIG

CONFIG_PATH = Path.home() / ".config" / "dashcorn" / "hook-config.yml"


def get_hook_config_path() -> Path:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    return CONFIG_PATH


def init_hook_template() -> bool:
    """
    Create hook-config.yml only if it does not exist.
    Returns True if file was created, False if it already existed.
    """
    path = get_hook_config_path()
    if path.exists():
        return False
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(DEFAULT_INJECT_CONFIG, f, allow_unicode=True)
    return True


def reset_hook_template():
    """
    Overwrite hook-config.yml with the default config.
    """
    path = get_hook_config_path()
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(DEFAULT_INJECT_CONFIG, f, allow_unicode=True)


def read_hook_template() -> str:
    """
    Return the raw YAML content as string.
    """
    path = get_hook_config_path()
    if not path.exists():
        init_hook_template()
    return path.read_text(encoding="utf-8")


def load_hook_template() -> dict:
    """
    Return the YAML content as Python dict.
    """
    return yaml.safe_load(read_hook_template())


def diff_hook_template() -> list[str]:
    """
    Return the unified diff (as list of lines) between
    the current config and the default.
    """
    current_yaml = read_hook_template()
    default_yaml = yaml.dump(DEFAULT_INJECT_CONFIG, allow_unicode=True)
    return list(difflib.unified_diff(
        default_yaml.splitlines(),
        current_yaml.splitlines(),
        fromfile="DEFAULT_INJECT_CONFIG",
        tofile=str(CONFIG_PATH),
        lineterm=""
    ))
