CREATE TABLE IF NOT EXISTS worker_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT,
    timestamp REAL,
    pid INTEGER,
    cpu REAL,
    memory INTEGER,
    status TEXT,
    role TEXT CHECK(role IN ('master', 'worker'))
);

CREATE TABLE IF NOT EXISTS http_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL,
    method TEXT,
    path TEXT,
    status INTEGER,
    duration REAL
);
