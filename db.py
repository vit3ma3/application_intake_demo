"""Хранилище заявок в SQLite."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import aiosqlite

import config

# Из каких статусов можно перейти в данный
ALLOWED_FROM = {
    "in_progress": ("new",),
    "closed": ("new", "in_progress"),
    "rejected": ("new", "in_progress"),
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    username      TEXT,
    full_name     TEXT,
    work_type     TEXT NOT NULL,
    description   TEXT NOT NULL,
    photo_file_id TEXT,
    phone         TEXT NOT NULL,
    call_time     TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'new',
    processed_by  TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
)
"""

_db_path = "requests.db"


def _now() -> datetime:
    return datetime.now(ZoneInfo(config.TIMEZONE)).replace(tzinfo=None, microsecond=0)


def _connect() -> aiosqlite.Connection:
    return aiosqlite.connect(_db_path)


async def init(path: str) -> None:
    global _db_path
    _db_path = path
    async with _connect() as db:
        await db.execute(_SCHEMA)
        await db.commit()


async def add_request(
    *,
    user_id: int,
    username: str | None,
    full_name: str,
    work_type: str,
    description: str,
    photo_file_id: str | None,
    phone: str,
    call_time: str,
) -> int:
    now = _now().isoformat(sep=" ")
    async with _connect() as db:
        cursor = await db.execute(
            "INSERT INTO requests (user_id, username, full_name, work_type, description,"
            " photo_file_id, phone, call_time, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, full_name, work_type, description,
             photo_file_id, phone, call_time, now, now),
        )
        await db.commit()
        return cursor.lastrowid


async def get_request(request_id: int) -> dict | None:
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_status(request_id: int, status: str, processed_by: str) -> bool:
    """Меняет статус, если переход допустим. Возвращает False, если статус уже другой."""
    allowed = ALLOWED_FROM[status]
    placeholders = ", ".join("?" * len(allowed))
    async with _connect() as db:
        cursor = await db.execute(
            f"UPDATE requests SET status = ?, processed_by = ?, updated_at = ?"
            f" WHERE id = ? AND status IN ({placeholders})",
            (status, processed_by, _now().isoformat(sep=" "), request_id, *allowed),
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_stats() -> dict:
    today = _now().date()
    week_start = today - timedelta(days=6)
    async with _connect() as db:
        async def count(where: str = "1", *args) -> int:
            cursor = await db.execute(f"SELECT COUNT(*) FROM requests WHERE {where}", args)
            return (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT status, COUNT(*) FROM requests GROUP BY status")
        by_status = dict(await cursor.fetchall())
        return {
            "today": await count("created_at >= ?", today.isoformat()),
            "week": await count("created_at >= ?", week_start.isoformat()),
            "total": await count(),
            "by_status": by_status,
        }


async def get_all_requests() -> list[dict]:
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM requests ORDER BY id")
        return [dict(row) for row in await cursor.fetchall()]
