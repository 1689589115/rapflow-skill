"""歌词清洗模块测试。"""

from __future__ import annotations

from crawler.cleaner import (
    clean_lyrics,
    remove_ads_and_platform_watermark,
    remove_empty_lines,
    remove_timestamp,
    split_sections,
)


def test_remove_timestamp() -> None:
    raw = "[00:12.34] 这是一句歌词\n[0:01] 另一句"
    result = remove_timestamp(raw)
    assert "00:12.34" not in result
    assert "0:01" not in result
    assert "这是一句歌词" in result
    assert "另一句" in result


def test_remove_ads() -> None:
    raw = (
        "[00:00.00]Produced and engineered by XYZ\n"
        "[00:05.00]这是一句歌词\n"
        "Lyrics powered by genius.com\n"
        "[Advertisement]\n"
        "听歌不收费 · 网易云音乐\n"
        "[00:10.00]第二句歌词"
    )
    result = remove_ads_and_platform_watermark(raw)
    assert "Produced and engineered" not in result
    assert "Lyrics powered by" not in result
    assert "[Advertisement]" not in result
    assert "听歌不收费" not in result
    assert "这是一句歌词" in result
    assert "第二句歌词" in result


def test_split_sections() -> None:
    raw = (
        "[Verse]\n"
        "第一段歌词\n"
        "第二段歌词\n"
        "[Hook]\n"
        "副歌部分\n"
        "[Chorus]\n"
        "合唱部分\n"
        "无标记的行"
    )
    sections = split_sections(raw)
    assert "verse" in sections
    assert "hook" in sections
    assert "chorus" in sections
    assert "第一段歌词" in sections["verse"]
    assert "副歌部分" in sections["hook"]
    assert "合唱部分" in sections["chorus"]
    assert "无标记的行" in sections["chorus"]


def test_empty_lines_collapsed() -> None:
    raw = "行一\n\n\n\n\n行二"
    result = remove_empty_lines(raw)
    assert result == "行一\n\n行二"


def test_clean_lyrics_pipeline() -> None:
    raw = (
        "[00:00.00]Produced by ABC\n"
        "[00:05.00]这是一句歌词\n"
        "\n\n\n\n"
        "[00:10.00]第二句歌词"
    )
    result = clean_lyrics(raw)
    assert "[00:00.00]" not in result
    assert "Produced by ABC" not in result
    assert "这是一句歌词" in result
    assert "第二句歌词" in result
    assert "\n\n\n" not in result


def test_split_sections_without_markers() -> None:
    raw = "第一行\n第二行\n第三行"
    sections = split_sections(raw)
    assert "main" in sections
    assert "第一行" in sections["main"]
