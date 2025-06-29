import os
import tempfile
from textwrap import dedent

import pytest

from dashcorn.command.code_hook_injector import (
    insert_middleware_and_imports,
    inject_middlewares_to_source_file,
    insert_lifecycle_triggers_to_fastapi,
    inject_lifecycle_to_source_file,
)


DEFAULT_INJECT_CONFIG = {
    "middleware": {
        "imports": ["from myproject.middleware import log_middleware"],
        "lines": ["<name_of_app>.add_middleware(log_middleware)"]
    },
    "lifecycle": {
        "imports": ["from myapp.hooks import startup_hook, shutdown_hook"],
        "on_startup": ["startup_hook"],
        "on_shutdown": ["shutdown_hook"]
    }
}


@pytest.fixture
def sample_code():
    return dedent("""
        from fastapi import FastAPI

        app = FastAPI()
    """)


def test_insert_middleware_and_imports(sample_code):
    updated = insert_middleware_and_imports(
        source_code=sample_code,
        import_statements=DEFAULT_INJECT_CONFIG["middleware"]["imports"],
        middleware_lines=DEFAULT_INJECT_CONFIG["middleware"]["lines"],
    )

    assert "app.add_middleware(log_middleware)" in updated
    assert "from myproject.middleware import log_middleware" in updated


def test_inject_middlewares_to_source_file(sample_code):
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "main.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(sample_code)

        inject_middlewares_to_source_file(
            file_path,
            config=DEFAULT_INJECT_CONFIG,
            backup=True,
        )

        # Nội dung mới có middleware
        with open(file_path, "r", encoding="utf-8") as f:
            updated = f.read()
        assert "app.add_middleware(log_middleware)" in updated

        # File .bak vẫn giữ nội dung gốc
        backup_path = file_path + ".bak"
        assert os.path.exists(backup_path)
        with open(backup_path, "r", encoding="utf-8") as f:
            backup = f.read()
        assert backup.strip() == sample_code.strip()


def test_inject_middlewares_file_not_found():
    with pytest.raises(FileNotFoundError):
        inject_middlewares_to_source_file("/nonexistent.py")


def test_insert_lifecycle_triggers_to_fastapi(sample_code):
    updated = insert_lifecycle_triggers_to_fastapi(
        source_code=sample_code,
        import_statements=["from myapp.hooks import startup_hook, shutdown_hook"],
        on_startup_triggers=["startup_hook"],
        on_shutdown_triggers=["shutdown_hook"],
    )

    assert "on_startup=[startup_hook]" in updated
    assert "on_shutdown=[shutdown_hook]" in updated
    assert "from myapp.hooks import startup_hook, shutdown_hook" in updated


def test_inject_lifecycle_to_source_file_creates_backup(sample_code):
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "main.py")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(sample_code)

        inject_lifecycle_to_source_file(
            file_path=file_path,
            config=DEFAULT_INJECT_CONFIG,
            backup=True
        )

        with open(file_path, "r", encoding="utf-8") as f:
            updated = f.read()

        assert "on_startup=[startup_hook]" in updated
        assert "on_shutdown=[shutdown_hook]" in updated

        # Backup exists and is original
        backup_path = file_path + ".bak"
        assert os.path.exists(backup_path)
        with open(backup_path, "r", encoding="utf-8") as f:
            assert f.read().strip() == sample_code.strip()


def test_inject_lifecycle_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        inject_lifecycle_to_source_file("/nonexistent/file.py")
