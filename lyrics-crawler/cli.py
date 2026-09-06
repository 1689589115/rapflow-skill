"""CLI 入口 — 提供 crawl / import / search / corpus 四个子命令。

用法示例：
    python cli.py crawl --artist "Jony J" --song "我的音乐"
    python cli.py search --artist "Jony J"
    python cli.py corpus --artist "Jony J"
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import logging
import os
import sys
from typing import Optional

# ── Windows UTF-8 output fix ──────────────────────────────────────────────
# On Windows, sys.stdout may be wrapped in a GBK TextIOWrapper.
# Force UTF-8 so Chinese characters render correctly in all terminals.
if sys.platform == 'win32':
    _enc = getattr(sys.stdout, 'encoding', '') or ''
    if _enc.lower() not in ('utf-8', 'utf8'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
# ──────────────────────────────────────────────────────────────────────────

from crawler.client import CrawlerClient
from crawler.extractor import LyricsExtractor
from crawler.sources.genius import GeniusSource
from crawler.sources.netease import NeteaseSource
from crawler.sources.musicazi import MusicaziSource
from crawler.sources.lrc_cx import LrcCXSource
from crawler.sources.manual_source import ManualLyricSource
from crawler.sources.search_fallback import GoogleSearchFallbackSource
from crawler.database import LyricsDB, DEFAULT_DB_PATH

# 添加 src 目录到路径
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from src.llm_analyzer import LLMAnalyzer
from src.analysis_adapter import AnalysisAdapter
from src.profile_builder import ProfileBuilder

logger = logging.getLogger(__name__)

# 输出数据目录（CLI 运行目录的 data/ 子目录）
_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _ensure_data_dir() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)


def _print_result(result: Optional[dict]) -> None:
    """格式化打印爬取结果摘要。"""
    if result is None:
        print("未获取到歌词，请检查歌手名/歌名或稍后重试。", file=sys.stderr)
        return
    print(f"歌手 : {result.get('artist')}")
    print(f"歌名 : {result.get('song')}")
    print(f"来源 : {result.get('source')}")
    print(f"置信度: {result.get('confidence'):.2f}")
    print(f"URL  : {result.get('url')}")
    print(f"专辑 : {result.get('album') or 'N/A'}")
    lyrics = result.get("lyrics", "")
    line_count = len([l for l in lyrics.splitlines() if l.strip()])
    print(f"歌词行数: {line_count}")


def cmd_crawl(args: argparse.Namespace) -> int:
    """执行 crawl 子命令：抓取歌词并存入数据库。"""
    artist = args.artist.strip()
    song = args.song.strip()
    if not artist or not song:
        print("错误：--artist 和 --song 不能为空", file=sys.stderr)
        return 1

    _ensure_data_dir()
    db = LyricsDB(os.path.join(_DATA_DIR, "lyrics_corpus.db"))

    try:
        client = CrawlerClient()
        extractor = LyricsExtractor(
            LrcCXSource(client),
            GeniusSource(client),
            NeteaseSource(client),
            MusicaziSource(client),
            GoogleSearchFallbackSource(client),
        )
        result = asyncio.run(extractor.crawl(artist, song))
        _print_result(result)

        if result is not None:
            db.insert(result)
            print(f"\n已存入数据库。")
            return 0
        return 1
    finally:
        db.close()


def cmd_search(args: argparse.Namespace) -> int:
    """执行 search 子命令：查询数据库中已收录的歌手歌曲列表。"""
    artist = args.artist.strip()
    if not artist:
        print("错误：--artist 不能为空", file=sys.stderr)
        return 1

    _ensure_data_dir()
    db = LyricsDB(os.path.join(_DATA_DIR, "lyrics_corpus.db"))

    try:
        rows = db.query_by_artist(artist)
        if not rows:
            print(f"未找到歌手 '{artist}' 的歌词记录。")
            return 0

        print("Songs found: " + str(len(rows)))
        print(f"{'歌名':<30} {'来源':<20} {'年份':<10} {'置信度'}")
        print("-" * 75)
        for row in rows:
            year = (row.release_date or "")[:4] if row.release_date else ""
            conf = f"{row.confidence:.2f}" if row.confidence else "N/A"
            song_name = (row.song or "")[:28]
            source_name = (row.source or "")[:18]
            print(f"{song_name:<30} {source_name:<20} {year:<10} {conf}")
        return 0
    finally:
        db.close()


def cmd_corpus(args: argparse.Namespace) -> int:
    """执行 corpus 子命令：导出歌手全量歌词为文本文件。"""
    artist = args.artist.strip()
    if not artist:
        print("错误：--artist 不能为空", file=sys.stderr)
        return 1

    _ensure_data_dir()
    db = LyricsDB(os.path.join(_DATA_DIR, "lyrics_corpus.db"))

    try:
        out_path = os.path.join(_DATA_DIR, f"{artist}_corpus.txt")
        line_count = db.export_corpus(artist, out_path)
        if line_count == 0:
            print(f"未找到歌手 '{artist}' 的歌词记录。")
            return 0

        # 统计文件行数
        with open(out_path, encoding="utf-8") as f:
            total = sum(1 for _ in f)
        print(f"歌词文件: {out_path}")
        print(f"总行数  : {total}")
        print(f"歌词行数: {line_count}")
        return 0
    finally:
        db.close()



def cmd_import(args: argparse.Namespace) -> int:
    """执行 import 子命令：从本地文件导入歌词并存入数据库。"""
    artist = args.artist.strip()
    song = args.song.strip()
    file_path = args.file

    if not artist or not song:
        print("错误：--artist 和 --song 不能为空", file=sys.stderr)
        return 1

    if not file_path:
        print("错误：--file 参数不能为空", file=sys.stderr)
        return 1

    # 读取歌词文件
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text_content = f.read()
    except FileNotFoundError:
        print(f"错误：找不到文件 '{file_path}'", file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        print("错误：文件编码不是 UTF-8，请转换为 UTF-8 后重试", file=sys.stderr)
        return 1

    if not text_content.strip():
        print("错误：歌词文件内容为空", file=sys.stderr)
        return 1

    _ensure_data_dir()
    db = LyricsDB(os.path.join(_DATA_DIR, "lyrics_corpus.db"))

    try:
        # 使用 ManualLyricSource 导入
        source = ManualLyricSource()
        source.set_text(artist, song, text_content)

        result = asyncio.run(source.search_lyrics(artist, song))
        _print_result(result)

        if result is not None:
            db.insert(result)
            print(f"已存入数据库。")
            return 0
        return 1
    finally:
        db.close()




def cmd_analyze(args: argparse.Namespace) -> int:
    """执行 analyze 子命令：分析歌词并生成专业解说。"""
    artist = args.artist.strip()
    song = args.song.strip()
    
    if not artist or not song:
        print("错误：--artist 和 --song 不能为空", file=sys.stderr)
        return 1
    
    _ensure_data_dir()
    db = LyricsDB(os.path.join(_DATA_DIR, "lyrics_corpus.db"))
    
    try:
        # 从数据库获取歌词
        row = db.query_one(artist, song, args.source)
        if row is None:
            print(f"未找到歌曲 '{artist} - {song}' (source={args.source})")
            return 1
        
        lyrics = row.clean_lyrics or row.raw_lyrics or ""
        if not lyrics:
            print(f"歌曲 '{artist} - {song}' 没有歌词内容")
            return 1
        
        print(f"歌手 : {row.artist}")
        print(f"歌名 : {row.song}")
        print(f"来源 : {row.source}")
        print(f"歌词长度: {len(lyrics)} 字符")
        print("")
        
        # 调用三路分析器
        print("运行技术分析...")
        adapter = AnalysisAdapter()
        analysis_result = adapter.analyze(lyrics, artist=artist, song=song)
        
        print("技术分析结果:")
        print(f"  押韵密度: {analysis_result['rhyme']['rhyme_density']}")
        print(f"  Flow style: {analysis_result['flow'].get('style', 'N/A')}")
        print(f"  声调匹配率: {analysis_result['tonal']['tonal_match_rate']}")
        print("")
        
        # 调用 LLM 生成解说
        print("生成专业解说...")
        print("")
        print("=" * 80)
        
        analyzer = LLMAnalyzer(model=args.model)
        report = analyzer.analyze(lyrics, analysis_result, artist=artist, song=song)
        print(report)
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"分析失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1




def cmd_profile(args: argparse.Namespace) -> int:
    """执行 profile 子命令：生成歌手风格档案。"""
    artist = args.artist.strip()
    if not artist:
        print("错误：--artist 不能为空", file=sys.stderr)
        return 1
    
    _ensure_data_dir()
    db = LyricsDB(os.path.join(_DATA_DIR, "lyrics_corpus.db"))
    
    try:
        # 获取歌手的歌曲列表
        rows = db.query_by_artist(artist)
        if not rows:
            print(f"未找到歌手 '{artist}' 的歌词记录")
            return 1
        
        print(f"歌手: {artist}")
        print(f"歌曲数量: {len(rows)}")
        print("")
        
        # 分析第一首歌作为代表
        first_row = rows[0]
        lyrics = first_row.clean_lyrics or first_row.raw_lyrics or ""
        
        if not lyrics:
            print(f"歌曲 '{first_row.song}' 没有歌词内容")
            return 1
        
        print(f"分析歌曲: {first_row.song}")
        print(f"歌词长度: {len(lyrics)} 字符")
        print("")
        
        # 运行技术分析
        print("运行技术分析...")
        adapter = AnalysisAdapter()
        analysis_result = adapter.analyze(lyrics, artist=artist, song=first_row.song)
        
        # 生成 Profile
        print("生成风格档案...")
        profile_builder = ProfileBuilder()
        profile = profile_builder.build(artist, first_row.song, analysis_result)
        
        # 打印 Profile
        print("")
        print("=" * 80)
        print("风格档案")
        print("=" * 80)
        print(json.dumps(profile, ensure_ascii=False, indent=2))
        
        return 0
        
    except Exception as e:
        print(f"分析失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main(argv: Optional[list[str]] = None) -> int:
    """CLI 入口函数。"""
    parser = argparse.ArgumentParser(
        prog="lyrics-crawler",
        description="中文说唱歌词爬虫引擎 — 抓取、清洗、存储歌词数据",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # crawl: 抓取歌词
    p_crawl = sub.add_parser("crawl", help="抓取指定歌手的歌词并存入数据库")
    p_crawl.add_argument("--artist", required=True, help="歌手名")
    p_crawl.add_argument("--song", required=True, help="歌名")
    p_crawl.add_argument(
        "--source",
        choices=["lrc_cx", "genius", "netease", "musicazi", "manual", "fallback", "all"],
        default="all",
        help="指定歌词源（默认 all，并发使用所有源）",
    )

    # search: 查询数据库
    p_search = sub.add_parser("search", help="查询数据库中已收录的歌手歌曲")
    p_search.add_argument("--artist", required=True, help="歌手名")

    # corpus: 导出歌词
    p_corpus = sub.add_parser("corpus", help="导出指定歌手的全量歌词为文本文件")
    p_corpus.add_argument("--artist", required=True, help="歌手名")

    # analyze: 分析歌词
    p_analyze = sub.add_parser("analyze", help="分析歌词并生成专业解说")
    p_analyze.add_argument("--artist", required=True, help="歌手名")
    p_analyze.add_argument("--song", required=True, help="歌名")
    p_analyze.add_argument(
        "--source",
        default="github_dataset",
        help="歌词来源（默认: github_dataset）",
    )
    p_analyze.add_argument(
        "--model",
        default="mock",
        choices=["mock", "gpt-4", "gpt-4o", "claude-3-opus", "deepseek-chat"],
        help="LLM 模型（默认: mock）",
    )

    # profile: 生成风格档案
    p_profile = sub.add_parser("profile", help="生成歌手风格档案")
    p_profile.add_argument("--artist", required=True, help="歌手名")

    args = parser.parse_args(argv)

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    cmd_map = {
        "crawl": cmd_crawl,
        "import": cmd_import,
        "search": cmd_search,
        "corpus": cmd_corpus,
        "analyze": cmd_analyze,
        "profile": cmd_profile,
    }
    return cmd_map[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
