import yaml
import pytest

from pathlib import Path

from dashcorn.command import hook_template_config as hooks
from dashcorn.command.code_hook_injector import DEFAULT_INJECT_CONFIG


@pytest.fixture(autouse=True)
def mock_config_dir(tmp_path, monkeypatch):
    """
    Redirect ~/.config/dashcorn to a temporary path for isolated testing.
    """
    fake_config_path = tmp_path / "dashcorn"
    monkeypatch.setattr(hooks, "CONFIG_PATH", fake_config_path / "hook-template.yaml")
    yield


def test_init_creates_file():
    path = hooks.get_hook_config_path()
    assert not path.exists()
    created = hooks.init_hook_template()
    assert created
    assert path.exists()

    # Calling again should not overwrite
    created_again = hooks.init_hook_template()
    assert not created_again


def test_reset_overwrites_file():
    path = hooks.get_hook_config_path()
    hooks.init_hook_template()

    # Write custom content
    path.write_text("custom: true")

    hooks.reset_hook_template()
    content = yaml.safe_load(path.read_text())
    assert content == DEFAULT_INJECT_CONFIG


def test_read_and_load_match():
    hooks.reset_hook_template()
    raw = hooks.read_hook_template()
    data = hooks.load_hook_template()
    assert yaml.safe_load(raw) == data
    assert data == DEFAULT_INJECT_CONFIG


def test_diff_returns_empty_for_default():
    hooks.reset_hook_template()
    diff = hooks.diff_hook_template()
    assert diff == []


def test_diff_detects_change():
    hooks.reset_hook_template()
    path = hooks.get_hook_config_path()
    path.write_text("modified: true")

    diff = hooks.diff_hook_template()
    assert any("modified: true" in line for line in diff)
