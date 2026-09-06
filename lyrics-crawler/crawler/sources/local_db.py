"""本地 SQLite 数据库歌词源 — 作为 lrc.cx API 失败时的备选。

从 lyrics-crawler/data/lyrics_corpus.db 查询歌词，匹配逻辑：
1. 精确匹配 artist + song
2. 大小写不敏感模糊匹配（song 必须是完整关键词，不能是单字子串）
3. 如果歌手+歌名都无法精确匹配，则拒绝返回，避免返回错误歌词
"""

from __future__ import annotations

import logging
import sqlite3
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class LocalDbSource:
    """从本地 SQLite 数据库获取歌词的备选源。"""

    NAME = "local_db"
    # 最短搜索关键词长度，少于此长度不执行模糊匹配（防止单字匹配返回错误结果）
    _MIN_KEYWORD_LEN = 2

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is not None:
            self._db_path = str(db_path)
        else:
            # 从项目根目录定位数据库
            # __file__ = .../crawler/sources/local_db.py
            # parent.parent.parent.parent = project root
            _root = Path(__file__).resolve().parent.parent.parent.parent
            self._db_path = str(_root / "lyrics-crawler" / "data" / "lyrics_corpus.db")

    def _normalize_text(self, text: str) -> str:
        """标准化文本：去除空格、标点、转小写。"""
        text = text.lower().strip()
        text = re.sub(r'[\s\W_]+', '', text)
        return text

    def search_lyrics(self, artist: str, song: str) -> Optional[dict]:
        """从本地数据库搜索歌词。

        参数：
            artist: 歌手名
            song: 歌名

        返回：
            歌词信息字典，结构同 LrcCXSource.search_lyrics
            如果没搜到或出错返回 None。
        """
        artist_norm = self._normalize_text(artist)
        song_norm = self._normalize_text(song)

        # 防御：空输入直接返回，不做数据库查询
        if not artist_norm or not song_norm:
            logger.info("LocalDbSource: empty input, skip search")
            return None

        try:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # ── 第一优先：精确匹配（大小写不敏感）────────────────────
            c.execute(
                "SELECT artist, song, raw_lyrics, clean_lyrics, source, confidence, url, album "
                "FROM lyrics "
                "WHERE LOWER(TRIM(artist)) = ? AND LOWER(TRIM(song)) = ?",
                (artist.lower().strip(), song.lower().strip()),
            )
            row = c.fetchone()

            # ── 第二优先：规范化后精确匹配（处理空格、大小写差异）──────
            if not row and len(artist_norm) >= self._MIN_KEYWORD_LEN and len(song_norm) >= self._MIN_KEYWORD_LEN:
                c.execute(
                    "SELECT artist, song, raw_lyrics, clean_lyrics, source, confidence, url, album "
                    "FROM lyrics "
                    "WHERE ? LIKE '%' || LOWER(TRIM(artist)) || '%' "
                    "AND ? LIKE '%' || LOWER(TRIM(song)) || '%'",
                    (artist_norm, song_norm),
                )
                row = c.fetchone()

            # ── 第三优先：只按歌名匹配（含歌手名中至少一个字符）──────
            # 限制：歌名必须 >= 2 字符，且结果必须包含歌手名中的字符
            if not row and len(song_norm) >= self._MIN_KEYWORD_LEN:
                # 先取歌名最匹配的 top 3
                c.execute(
                    "SELECT artist, song, raw_lyrics, clean_lyrics, source, confidence, url, album "
                    "FROM lyrics "
                    "WHERE ? LIKE '%' || LOWER(TRIM(song)) || '%'"
                    "ORDER BY LENGTH(clean_lyrics) DESC LIMIT 5",
                    (song_norm,),
                )
                candidates = c.fetchall()
                # 过滤：结果必须包含歌手名中的字符（防止歌手完全不对但歌名子串碰巧匹配）
                for candidate in candidates:
                    cand_artist_norm = self._normalize_text(candidate["artist"] or "")
                    # 至少有一个字符在歌手名中出现
                    if artist_norm and cand_artist_norm and any(c in cand_artist_norm for c in artist_norm if len(c) >= 1):
                        row = candidate
                        break
                # 如果歌手名太短无法验证，且只有一首候选，也接受
                if not row and len(candidates) == 1 and len(artist_norm) < self._MIN_KEYWORD_LEN:
                    row = candidates[0]

            conn.close()

            if not row:
                logger.info("LocalDbSource: no lyrics found for '%s - %s'", artist, song)
                return None

            lyrics = row["clean_lyrics"] or row["raw_lyrics"] or ""
            if not lyrics:
                return None

            return {
                "artist": row["artist"] or artist,
                "song": row["song"] or song,
                "lyrics": lyrics,
                "raw_lyrics": row["raw_lyrics"] or lyrics,
                "url": row["url"] or "",
                "album": row["album"] or "",
                "source": self.NAME,
                "confidence": 0.7,
            }

        except Exception as e:
            logger.warning("LocalDbSource: error searching '%s - %s': %r", artist, song, e)
            return None
