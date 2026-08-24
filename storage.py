from abc import ABC, abstractmethod
import aiofiles
import json
import csv
import io
import aiosqlite


class DataStorage(ABC):
    @abstractmethod
    async def save(self, data: dict) -> None:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...


class JSONStorage(DataStorage):
    def __init__(self, filepath: str):
        self.filepath = filepath

    async def save(self, data: dict) -> None:
        line = json.dumps(data, ensure_ascii=False, default=str)
        async with aiofiles.open(self.filepath, mode="a", encoding="utf-8") as f:
            await f.write(line + "\n")

    async def close(self) -> None:
        pass

class CSVStorage(DataStorage):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._header_written = False

    async def save(self, data: dict) -> None:
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        if not self._header_written:
            writer.writerow(list(data.keys()))
            self._header_written = True

        writer.writerow(list(data.values()))

        async with aiofiles.open(self.filepath, mode="a", encoding="utf-8", newline="") as f:
            await f.write(buffer.getvalue())

    async def close(self) -> None:
        pass


class SQLiteStorage(DataStorage):
    def __init__(self, filepath: str, batch_size: int = 5):
        self.filepath = filepath
        self._db = None
        self._buffer = []
        self._batch_size = batch_size

    async def init_db(self) -> None:
        self._db = await aiosqlite.connect(self.filepath)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                title TEXT,
                text TEXT,
                links TEXT,
                metadata TEXT,
                crawled_at TEXT,
                status_code INTEGER,
                content_type TEXT
            )
        """)
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_url ON pages(url)"
        )
        await self._db.commit()

    async def save(self, data: dict) -> None:
        await self._ensure_db()
        self._buffer.append((
            data.get("url"),
            data.get("title"),
            data.get("text"),
            json.dumps(data.get("links", []), ensure_ascii=False),
            json.dumps(data.get("metadata", {}), ensure_ascii=False),
            data.get("crawled_at"),
            data.get("status_code"),
            data.get("content_type"),
        ))
        if len(self._buffer) >= self._batch_size:
            await self._flush()

    async def _flush(self) -> None:
        if not self._buffer:
            return
        await self._db.executemany(
            """INSERT INTO pages
               (url, title, text, links, metadata, crawled_at, status_code, content_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            self._buffer,
        )
        await self._db.commit()
        self._buffer = []

    async def close(self) -> None:
        await self._flush()
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def _ensure_db(self) -> None:
        if self._db is None:
            await self.init_db()