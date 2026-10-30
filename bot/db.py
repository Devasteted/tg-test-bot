import os
from datetime import datetime, timezone

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY,
    username    TEXT,
    full_name   TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS requests (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    service     TEXT NOT NULL,
    name        TEXT NOT NULL,
    phone       TEXT NOT NULL,
    comment     TEXT,
    created_at  TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class Database:
    def __init__(self, path: str):
        self.path = path

    async def init(self) -> None:
        folder = os.path.dirname(self.path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(SCHEMA)
            await db.commit()

    async def add_user(self, user_id: int, username: str | None, full_name: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO users (id, username, full_name, created_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET username = excluded.username, full_name = excluded.full_name",
                (user_id, username, full_name, _now()),
            )
            await db.commit()

    async def add_request(
        self, user_id: int, service: str, name: str, phone: str, comment: str | None
    ) -> int:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "INSERT INTO requests (user_id, service, name, phone, comment, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, service, name, phone, comment, _now()),
            )
            await db.commit()
            return cur.lastrowid

    async def last_requests(self, limit: int = 10) -> list[aiosqlite.Row]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM requests ORDER BY id DESC LIMIT ?", (limit,)
            )
            return await cur.fetchall()

    async def user_ids(self) -> list[int]:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT id FROM users")
            return [row[0] for row in await cur.fetchall()]

    async def stats(self) -> dict[str, int]:
        async with aiosqlite.connect(self.path) as db:
            users = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
            total = (await (await db.execute("SELECT COUNT(*) FROM requests")).fetchone())[0]
            today = (
                await (
                    await db.execute(
                        "SELECT COUNT(*) FROM requests WHERE date(created_at) = date('now')"
                    )
                ).fetchone()
            )[0]
            return {"users": users, "requests": total, "today": today}
