#!/usr/bin/env python3
import argparse, json, logging, sqlite3, sys, io
from pathlib import Path
from collections import Counter

# Windows UTF-8 output fix (same pattern as cli.py)
if sys.platform == 'win32':
    _enc = getattr(sys.stdout, 'encoding', '') or ''
    if _enc.lower() not in ('utf-8', 'utf8'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("rapflow_mcp")

_DB_PATH = Path(__file__).parent / "lyrics-crawler" / "data" / "lyrics_corpus.db"
MCP_TOOLS = {"stats": "显示数据库统计", "search": "搜索歌词", "analyze": "分析歌词", "artists": "热门歌手"}

def get_conn():
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def cmd_stats():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM lyrics"); total = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT artist) FROM lyrics"); artists = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT artist || '+' || song) FROM lyrics"); unique = c.fetchone()[0]
    c.execute("SELECT source, COUNT(DISTINCT artist || '+' || song) as u, COUNT(*) as t FROM lyrics GROUP BY source ORDER BY u DESC")
    sources = [{"source": r["source"], "unique_songs": r["u"], "total": r["t"]} for r in c.fetchall()]
    conn.close()
    return {"total_rows": total, "unique_songs": unique, "total_artists": artists, "target": 10000, "gap": max(0, 10000-unique), "sources": sources}

def cmd_search(artist, song=""):
    conn = get_conn(); c = conn.cursor()
    if song: c.execute("SELECT artist, song, source, confidence, raw_lyrics FROM lyrics WHERE artist LIKE ? AND song LIKE ? LIMIT 10", (f"%{artist}%", f"%{song}%"))
    else: c.execute("SELECT artist, song, source, confidence, raw_lyrics FROM lyrics WHERE artist LIKE ? OR song LIKE ? LIMIT 50", (f"%{artist}%", f"%{artist}%"))
    rows = c.fetchall(); conn.close()
    return {"count": len(rows), "results": [{"artist": r["artist"], "song": r["song"], "source": r["source"], "confidence": r["confidence"], "lyrics_preview": (r["raw_lyrics"] or "")[:200]+"..." if r["raw_lyrics"] else ""} for r in rows]}

def cmd_analyze(artist, song):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT artist, song, source, raw_lyrics, clean_lyrics FROM lyrics WHERE artist LIKE ? AND song LIKE ? LIMIT 1", (f"%{artist}%", f"%{song}%"))
    row = c.fetchone(); conn.close()
    if not row: return {"error": "未找到"}
    lyrics = row["clean_lyrics"] or row["raw_lyrics"] or ""
    if not lyrics: return {"error": "歌词为空"}
    lines = [l.strip() for l in lyrics.split(chr(10)) if l.strip()]
    rhyme_words = [line[-1] for line in lines if line]
    top_rhymes = Counter(rhyme_words).most_common(10)
    return {"artist": row["artist"], "song": row["song"], "source": row["source"], "stats": {"lines": len(lines), "chars": len(lyrics)}, "rhymes": top_rhymes, "preview": lyrics[:500]}

def cmd_artists(limit=10):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT artist, COUNT(DISTINCT song) as cnt FROM lyrics GROUP BY artist ORDER BY cnt DESC LIMIT ?", (limit,))
    rows = c.fetchall(); conn.close()
    return {"count": len(rows), "artists": [{"name": r["artist"], "songs": r["cnt"]} for r in rows]}

def handle(tool, args):
    if tool == "stats": return {"content": [{"type": "text", "text": json.dumps(cmd_stats(), ensure_ascii=False, indent=2)}]}
    elif tool == "search": return {"content": [{"type": "text", "text": json.dumps(cmd_search(**args), ensure_ascii=False, indent=2)}]}
    elif tool == "analyze": return {"content": [{"type": "text", "text": json.dumps(cmd_analyze(**args), ensure_ascii=False, indent=2)}]}
    elif tool == "artists": return {"content": [{"type": "text", "text": json.dumps(cmd_artists(**args), ensure_ascii=False, indent=2)}]}
    else: return {"error": "Unknown tool: " + tool}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["server", "cli"], default="cli")
    parser.add_argument("--tool", choices=list(MCP_TOOLS.keys()))
    parser.add_argument("--artist"); parser.add_argument("--song"); parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    if args.mode == "server":
        logger.info("RapFlow MCP Server started"); logger.info("Tools: " + ", ".join(MCP_TOOLS.keys())); return 0
    elif args.mode == "cli":
        if not args.tool: parser.print_help(); return 1
        tool_args = {}
        if args.tool in ("search", "analyze") and args.artist: tool_args["artist"] = args.artist
        if args.tool in ("search", "analyze") and args.song: tool_args["song"] = args.song
        if args.tool == "artists" and args.limit: tool_args["limit"] = args.limit
        result = handle(args.tool, tool_args)
        if "error" in result: print(json.dumps({"error": result["error"]}, ensure_ascii=False)); return 1
        else: print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    return 0

if __name__ == "__main__": sys.exit(main())
