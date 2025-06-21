import sqlite3
from pathlib import Path
from platformdirs import user_config_dir

APP_NAME = "dashcorn"
DEFAULT_DB_PATH = Path(user_config_dir(APP_NAME)) / "dashcorn.sqlite3"

_current_db_path: Path = DEFAULT_DB_PATH  # mutable global

def set_db_path(path: Path):
    global _current_db_path
    _current_db_path = path

def get_conn():
    _current_db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(_current_db_path)

def init_db():
    from pathlib import Path
    schema_file = Path(__file__).parent / "schema.sql"
    with open(schema_file) as f:
        sql = f.read()
    conn = get_conn()
    conn.executescript(sql)
    conn.commit()
    conn.close()

def save_worker_info(data: dict):
    hostname = data.get("hostname")
    timestamp = data.get("timestamp")
    master = data.get("master", {})
    workers = data.get("workers", [])

    conn = get_conn()
    cur = conn.cursor()

    # Save master process
    cur.execute("""
        INSERT INTO worker_metrics (hostname, timestamp, pid, cpu, memory, status, role)
        VALUES (?, ?, ?, ?, ?, ?, 'master')
    """, (
        hostname,
        timestamp,
        master.get("pid"),
        master.get("cpu"),
        master.get("memory"),
        "active"
    ))

    # Save each worker
    for w in workers:
        cur.execute("""
            INSERT INTO worker_metrics (hostname, timestamp, pid, cpu, memory, status, role)
            VALUES (?, ?, ?, ?, ?, ?, 'worker')
        """, (
            hostname,
            timestamp,
            w.get("pid"),
            w.get("cpu"),
            w.get("memory"),
            w.get("status")
        ))

    conn.commit()
    conn.close()

def save_http_metric(data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO http_metrics (timestamp, method, path, status, duration)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data.get("time"),
        data.get("method"),
        data.get("path"),
        data.get("status"),
        data.get("duration"),
    ))
    conn.commit()
    conn.close()
