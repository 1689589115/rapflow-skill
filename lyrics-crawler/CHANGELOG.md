# Changelog

All notable changes to the lyrics-crawler project will be documented in this file.

## [2026-08-08] - Module 1: Lyrics Crawler Engine

### Added
- **LrcCXSource adapter** (main lyrics source via `api.lrc.cx`)
  - API endpoint: `https://api.lrc.cx/lyrics`
  - Search parameters: `?artist={name}&song={title}`
  - Returns LRC format lyrics (timestamped)
  - Confidence: 0.9
  - All requests go through proxy (127.0.0.1:7897)

- **Bulk import script** (`scripts/bulk_import_github.py`)
  - Fetches artist JSON files from GitHub repository
  - Parses and inserts lyrics into SQLite database
  - Source: `github_dataset`, Confidence: 0.8
  - Duplicate protection via `(artist, song, source)` unique constraint

- **Analysis pipeline** (`scripts/analyze_corpus.py`)
  - Database statistics (total songs, artists, source distribution)
  - Corpus export for specific artists
  - Lyrics length analysis

- **Proxy support** for all HTTP requests
  - Client-side proxy configuration
  - Automatic proxy client management
  - Default proxy: `http://127.0.0.1:7897`

- **Deprecated sources** ( kept for compatibility, return None )
  - `GeniusSource`: Requires access token (not implemented)
  - `NeteaseSource`: AES encryption logic failed
  - `MusicaziSource`: Website unreachable in current network

### Modified
- `crawler/client.py`: Added proxy parameter support
- `crawler/sources/lrc_cx.py`: New main lyrics source adapter
- `crawler/sources/genius.py`: Marked as DEPRECATED
- `crawler/sources/netease.py`: Marked as DEPRECATED
- `crawler/sources/musicazi.py`: Marked as DEPRECATED
- `cli.py`: Updated to use LrcCXSource as primary source
- `crawler/__init__.py`: Updated exports and version to 0.3.0

### Statistics
- **Database**: 2,605 songs from 74 artists
  - github_dataset: 2,600 songs
  - lrc_cx: 1 song (Jony J - 我的音乐)
  - manual: 4 songs
- **Tests**: 35/35 passed
- **Corpus exported**:
  - Jony J: 3,293 lines (53 songs)
  - MC Hotdog: 4,084 lines (49 songs)

### Pipeline Status
- ✅ Crawl: Verified (lrc_cx works)
- ✅ Import: Verified (GitHub dataset bulk import)
- ✅ Search: Verified (database queries)
- ✅ Corpus: Verified (text export)

---

## [2026-08-07] - Initial Project Structure

### Added
- Core crawler modules
  - `crawler/client.py`: Async HTTP client with UA rotation
  - `crawler/cleaner.py`: Lyrics cleaning pipeline
  - `crawler/extractor.py`: Multi-source lyrics extractor
  - `crawler/database.py`: SQLite storage layer
  - `crawler/sources/base.py`: Abstract base class for sources
  - `crawler/sources/genius.py`: Genius.com adapter
  - `crawler/sources/netease.py`: Netease Music adapter
- CLI interface (`cli.py`)
  - `crawl`: Fetch lyrics from multiple sources
  - `import`: Import lyrics from local files
  - `search`: Query database by artist
  - `corpus`: Export corpus for an artist
- Test suite (11 tests)
- Project documentation
