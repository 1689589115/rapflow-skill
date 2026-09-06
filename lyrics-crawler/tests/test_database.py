"""数据库模块测试。使用内存数据库，不污染磁盘。"""

from __future__ import annotations

import os
import tempfile

from crawler.database import LyricsDB


def _make_sample_row() -> dict:
    return {
        "artist": "Test Artist",
        "song": "Test Song",
        "source": "netease",
        "url": "https://music.163.com/#/song?id=12345",
        "album": "Test Album",
        "release_date": "2024-01-01",
        "raw_lyrics": "[00:00.00]原始歌词\n[00:05.00]第二句",
        "lyrics": "原始歌词\n第二句",
        "confidence": 0.95,
    }


def test_insert_query() -> None:
    """测试插入后能正确查出来。"""
    with LyricsDB(":memory:") as db:
        data = _make_sample_row()
        db.insert(data)

        rows = db.query_by_artist("Test Artist")
        assert len(rows) == 1
        row = rows[0]
        assert row.artist == "Test Artist"
        assert row.song == "Test Song"
        assert row.source == "netease"
        assert row.confidence == 0.95
        assert row.url == "https://music.163.com/#/song?id=12345"


def test_duplicate_ignored() -> None:
    """测试同歌手+同歌名+同源不重复插入。"""
    with LyricsDB(":memory:") as db:
        data = _make_sample_row()
        first = db.insert(data)
        second = db.insert(data)

        assert first is True
        assert second is False  # 重复插入应被 IGNORE

        rows = db.query_by_artist("Test Artist")
        assert len(rows) == 1


def test_corpus_concatenation() -> None:
    """测试多条歌词能正确拼接导出。"""
    with LyricsDB(":memory:") as db:
        songs = [
            {
                **_make_sample_row(),
                "song": "Song A",
                "lyrics": "歌词A第一行\n歌词A第二行",
            },
            {
                **_make_sample_row(),
                "song": "Song B",
                "lyrics": "歌词B第一行\n歌词B第二行",
            },
        ]
        for s in songs:
            db.insert(s)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            tmp_path = f.name

        try:
            line_count = db.export_corpus("Test Artist", tmp_path)
            assert line_count > 0

            with open(tmp_path, encoding="utf-8") as f:
                content = f.read()
            assert "=======" in content
            assert "Song A" in content
            assert "Song B" in content
            assert "歌词A第一行" in content
            assert "歌词B第二行" in content
        finally:
            os.unlink(tmp_path)


def test_query_one() -> None:
    """测试单条查询。"""
    with LyricsDB(":memory:") as db:
        data = _make_sample_row()
        db.insert(data)

        row = db.query_one("Test Artist", "Test Song", "netease")
        assert row is not None
        assert row.song == "Test Song"

        # 不存在的组合应返回 None
        assert db.query_one("Unknown", "Unknown", "netease") is None


def test_empty_query() -> None:
    """测试空库查询不报错。"""
    with LyricsDB(":memory:") as db:
        rows = db.query_by_artist("Nobody")
        assert rows == []
