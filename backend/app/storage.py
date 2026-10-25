"""
Thread-safe JSON-file storage for the prototype.

Deliberately simple: one JSON file per collection, guarded by a lock,
atomic write via temp-file + rename. This is the "start with JSON storage"
stage from the build guide. Swapping this module for a PostGIS/Postgres
backed one later should not require changing the routers, only this file.
"""

import json
import os
import tempfile
import threading
import uuid
from datetime import datetime, timezone

from app.config import DATA_DIR

_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def _lock_for(name: str) -> threading.Lock:
    with _LOCKS_GUARD:
        if name not in _LOCKS:
            _LOCKS[name] = threading.Lock()
        return _LOCKS[name]


def _path(collection: str) -> str:
    return os.path.join(DATA_DIR, f"{collection}.json")


def _read_all(collection: str) -> dict:
    path = _path(collection)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        return json.loads(content) if content else {}


def _write_all(collection: str, data: dict) -> None:
    path = _path(collection)
    fd, tmp_path = tempfile.mkstemp(dir=DATA_DIR, prefix=f".{collection}_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def put(collection: str, record_id: str, record: dict) -> dict:
    lock = _lock_for(collection)
    with lock:
        data = _read_all(collection)
        data[record_id] = record
        _write_all(collection, data)
        return record


def get(collection: str, record_id: str) -> dict | None:
    lock = _lock_for(collection)
    with lock:
        data = _read_all(collection)
        return data.get(record_id)


def list_all(collection: str) -> list[dict]:
    lock = _lock_for(collection)
    with lock:
        data = _read_all(collection)
        return list(data.values())


def update(collection: str, record_id: str, patch: dict) -> dict | None:
    lock = _lock_for(collection)
    with lock:
        data = _read_all(collection)
        if record_id not in data:
            return None
        data[record_id].update(patch)
        _write_all(collection, data)
        return data[record_id]


def delete(collection: str, record_id: str) -> bool:
    lock = _lock_for(collection)
    with lock:
        data = _read_all(collection)
        if record_id not in data:
            return False
        del data[record_id]
        _write_all(collection, data)
        return True