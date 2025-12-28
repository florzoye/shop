import aiosqlite
from typing import Any, Iterable, Optional


class AsyncDatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def execute(
        self,
        query: str,
        params: Optional[dict] = None
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            await db.execute(query, params or {})
            await db.commit()

    async def executemany(
        self,
        query: str,
        params: Iterable[dict]
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            await db.executemany(query, params)
            await db.commit()

    async def fetchone(
        self,
        query: str,
        params: Optional[dict] = None
    ) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params or {}) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def fetchall(
        self,
        query: str,
        params: Optional[dict] = None
    ) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params or {}) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
