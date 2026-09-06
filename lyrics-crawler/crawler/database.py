"""SQLite 语料库模块。

使用标准库 sqlite3 存储歌词数据，支持：
- 按 (artist, song, source) 去重插入
- 按歌手查询所有已收录歌曲
- 按歌手导出全量歌词为文本文件
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# 语料库默认路径（data 目录下）
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "lyrics_corpus.db")

# 建表 SQL：lyrics 表存储每首歌词
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS lyrics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    artist      TEXT NOT NULL,
    song        TEXT NOT NULL,
    source      TEXT NOT NULL,
    url         TEXT,
    album       TEXT,
    release_date TEXT,
    raw_lyrics  TEXT,
    clean_lyrics TEXT,
    confidence  REAL,
    created_at  TEXT NOT NULL,
    UNIQUE(artist, song, source)
);
"""

# 按歌手查询索引
_CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_lyrics_artist
    ON lyrics(artist);
"""

# 插入语句
_INSERT_SQL = """
INSERT OR IGNORE INTO lyrics
    (artist, song, source, url, album, release_date, raw_lyrics, clean_lyrics, confidence, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# 查询某歌手所有歌曲
_SELECT_BY_ARTIST_SQL = """
SELECT artist, song, source, url, album, release_date, raw_lyrics, clean_lyrics, confidence, created_at
FROM lyrics WHERE artist = ? ORDER BY created_at DESC
"""

# 查询单条
_SELECT_ONE_SQL = """
SELECT artist, song, source, url, album, release_date, raw_lyrics, clean_lyrics, confidence, created_at
FROM lyrics WHERE artist = ? AND song = ? AND source = ?
"""


class LyricsRow:
    """将 sqlite3.Row 封装为更易访问的对象。"""

    __slots__ = ("_row",)

    def __init__(self, row: sqlite3.Row) -> None:
        self._row = row

    @property
    def artist(self) -> str:
        return self._row["artist"]

    @property
    def song(self) -> str:
        return self._row["song"]

    @property
    def source(self) -> str:
        return self._row["source"]

    @property
    def url(self) -> Optional[str]:
        return self._row["url"]

    @property
    def album(self) -> Optional[str]:
        return self._row["album"]

    @property
    def release_date(self) -> Optional[str]:
        return self._row["release_date"]

    @property
    def raw_lyrics(self) -> Optional[str]:
        return self._row["raw_lyrics"]

    @property
    def clean_lyrics(self) -> Optional[str]:
        return self._row["clean_lyrics"]

    @property
    def confidence(self) -> Optional[float]:
        return self._row["confidence"]

    @property
    def created_at(self) -> str:
        return self._row["created_at"]

    def to_dict(self) -> dict:
        return {
            "artist": self.artist,
            "song": self.song,
            "source": self.source,
            "url": self.url,
            "album": self.album,
            "release_date": self.release_date,
            "raw_lyrics": self.raw_lyrics,
            "clean_lyrics": self.clean_lyrics,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }


class LyricsDB:
    """歌词 SQLite 数据库，管理歌词的插入和查询。"""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        """初始化数据库连接。

        参数：
            db_path: SQLite 数据库文件路径，默认 data/lyrics_corpus.db
        """
        self._db_path = db_path
        # 确保 data 目录存在
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")  # 提升并发读写性能
        self._conn.execute(_CREATE_TABLE_SQL)
        self._conn.execute(_CREATE_INDEX_SQL)
        self._conn.commit()
        logger.info("Opened lyrics database at %s", db_path)

    def close(self) -> None:
        """关闭数据库连接。"""
        if self._conn:
            self._conn.close()

    def __enter__(self) -> "LyricsDB":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def insert(self, lyric_data: dict) -> bool:
        """将一条歌词记录写入数据库，重复记录自动忽略。

        参数：
            lyric_data: 与 LyricsSource.search_lyrics 返回格式一致的字典

        返回：
            True 表示成功插入，False 表示已存在（忽略）
        """
        now = datetime.now(timezone.utc).isoformat()
        try:
            # 先查询是否已存在，避免 INSERT OR IGNORE 后 total_changes 不可靠
            existing = self._conn.execute(
                "SELECT 1 FROM lyrics WHERE artist=? AND song=? AND source=?",
                (lyric_data.get("artist", ""), lyric_data.get("song", ""), lyric_data.get("source", "")),
            ).fetchone()
            if existing is not None:
                logger.info(
                    "Duplicate skipped: '%s - %s' from %s",
                    lyric_data.get("artist"),
                    lyric_data.get("song"),
                    lyric_data.get("source"),
                )
                return False
            self._conn.execute(
                _INSERT_SQL,
                (
                    lyric_data.get("artist", ""),
                    lyric_data.get("song", ""),
                    lyric_data.get("source", ""),
                    lyric_data.get("url"),
                    lyric_data.get("album"),
                    lyric_data.get("release_date"),
                    lyric_data.get("raw_lyrics"),
                    lyric_data.get("lyrics"),
                    lyric_data.get("confidence"),
                    now,
                ),
            )
            self._conn.commit()
            logger.info(
                "Inserted '%s - %s' from %s",
                lyric_data.get("artist"),
                lyric_data.get("song"),
                lyric_data.get("source"),
            )
            return True
        except sqlite3.Error as exc:
            logger.error("Failed to insert lyrics: %r", exc)
            return False

    def query_by_artist(self, artist: str) -> list[LyricsRow]:
        """查询指定歌手的所有歌词记录。"""
        cur = self._conn.execute(_SELECT_BY_ARTIST_SQL, (artist,))
        return [LyricsRow(row) for row in cur.fetchall()]

    def query_one(self, artist: str, song: str, source: str) -> Optional[LyricsRow]:
        """查询指定歌手+歌名+来源的單条记录。"""
        cur = self._conn.execute(_SELECT_ONE_SQL, (artist, song, source))
        row = cur.fetchone()
        return LyricsRow(row) if row else None

    def export_corpus(self, artist: str, output_path: str) -> int:
        """导出指定歌手的歌词到文本文件，返回写入的行数。

        每首歌之间用 '=======' 分隔，包含歌手、歌名、来源标注。
        """
        rows = self.query_by_artist(artist)
        if not rows:
            logger.warning("No lyrics found for artist '%s'", artist)
            return 0

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        lines: list[str] = []
        total_lyric_lines: int = 0
        for i, row in enumerate(rows):
            if i > 0:
                lines.append("=======")
            lines.append(f"# {row.artist} — {row.song} (via {row.source})")
            if row.clean_lyrics:
                lines.append(row.clean_lyrics)
                total_lyric_lines += len(row.clean_lyrics.splitlines())
            elif row.raw_lyrics:
                lines.append(row.raw_lyrics)
                total_lyric_lines += len(row.raw_lyrics.splitlines())
            else:
                lines.append("(no lyrics)")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        logger.info(
            "Exported %d songs for '%s' to %s", len(rows), artist, output_path
        )
        return total_lyric_lines
