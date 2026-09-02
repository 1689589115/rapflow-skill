# -*- coding: utf-8 -*-
'''NetEase Cloud Music adapter via Node.js NeteaseCloudMusicApi.'''

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from crawler.sources.base import LyricsSource

logger = logging.getLogger(__name__)

_NODE_PATHS = [r'D:\\node.js\\node.exe', r'C:\\Program Files\\nodejs\\node.exe', 'node']
_node_path: Optional[str] = None
_API_SCRIPT_DIR = Path(__file__).parent.parent.parent.parent / 'NeteaseCloudMusicApi'

def _find_node():
    for p in _NODE_PATHS:
        if os.path.isabs(p) and os.path.exists(p):
            return p
    try:
        r = subprocess.run(['where', 'node'], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return r.stdout.strip().split(chr(10))[0]
    except Exception:
        pass
    return None

def _get_node_path():
    global _node_path
    if _node_path is not None:
        return _node_path
    _node_path = _find_node()
    if _node_path:
        logger.info('Found Node.js: %s', _node_path)
    else:
        logger.warning('Node.js not found')
    return _node_path

class NeteaseSource(LyricsSource):
    NAME = 'netease'

    def __init__(self, client=None):
        self._node_path = _get_node_path()
        self._api_dir = str(_API_SCRIPT_DIR)

    def search_lyrics(self, artist, song):
        if not self._node_path:
            return None
        try:
            search_result = self._search(song)
            if not search_result:
                return None
            songs = search_result.get('result', {}).get('songs', [])
            if not songs:
                return None
            best = self._pick_best(songs, artist, song)
            if not best:
                return None
            song_id = best['id']
            song_name = best.get('name', song)
            artists = best.get('artists', [])
            artist_name = artists[0].get('name', artist) if artists else artist
            lyric_result = self._get_lyric(song_id)
            if not lyric_result:
                return {'artist': artist_name, 'song': song_name,
                    'lyrics': f'[Lyrics unavailable - id: {song_id}]',
                    'raw_lyrics': '',
                    'url': f'https://music.163.com/#/song?id={song_id}',
                    'album': '', 'source': self.NAME, 'confidence': 0.5}
            raw = lyric_result.get('lrc', '')
            if not raw or (isinstance(raw, dict) and not raw.get('lyric')):
                return None
            clean = self._clean_lrc(raw.get('lyric', '') if isinstance(raw, dict) else raw)
            return {'artist': artist_name, 'song': song_name,
                'lyrics': clean, 'raw_lyrics': raw,
                'url': f'https://music.163.com/#/song?id={song_id}',
                'album': best.get('album', {}).get('name', ''),
                'source': self.NAME, 'confidence': 0.95}
        except Exception as e:
            logger.warning('NeteaseSource error: %r', e)
            return None
    def _search(self, song):
        api = self._api_dir.replace(chr(92), chr(47))
        sq2 = chr(39)
        script = 'const N=require(' + sq2 + api + '/node_modules/NeteaseCloudMusicApi' + sq2 + ');'
        script += '(async()=>{try{const r=await N.search({keywords:' + sq2 + song + sq2 + ',type:1,limit:10});console.log(JSON.stringify(r));}'
        script += 'catch(e){console.log(JSON.stringify({error:e.message}));}})();'
        return self._run_node(script)

    def _get_lyric(self, song_id):
        api = self._api_dir.replace(chr(92), chr(47))
        sq2 = chr(39)
        script = 'const N=require(' + sq2 + api + '/node_modules/NeteaseCloudMusicApi' + sq2 + ');'
        script += '(async()=>{try{const r=await N.lyric({id:' + str(song_id) + '});console.log(JSON.stringify(r));}'
        script += 'catch(e){console.log(JSON.stringify({error:e.message}));}})();'
        return self._run_node(script)

    def _run_node(self, script):
        fd, spath = tempfile.mkstemp(suffix='.js', prefix='na_')
        os.close(fd)
        with open(spath, 'w', encoding='utf-8') as f:
            f.write(script)
        opath = spath + '.out'
        epath = spath + '.err'
        try:
            env = os.environ.copy()
            proxy = env.get('https_proxy') or env.get('http_proxy')
            if proxy:
                env['HTTPS_PROXY'] = proxy
                env['HTTP_PROXY'] = proxy
            with open(opath, 'w', encoding='utf-8') as of:
                with open(epath, 'w', encoding='utf-8') as ef:
                    subprocess.run([self._node_path, spath], stdout=of, stderr=ef, cwd=self._api_dir, env=env, timeout=15)
            with open(opath, 'r', encoding='utf-8') as f:
                output = f.read().strip()
            if not output:
                return None
            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                return None
            if data.get('error'):
                return None
            return data.get('body', data)
        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            logger.warning('Node script failed: %r', e)
            return None
        finally:
            for p in [spath, opath, epath]:
                try:
                    os.unlink(p)
                except OSError:
                    pass
    def _pick_best(self, songs, artist, song):
        sl = song.lower().strip()
        al = artist.lower().strip()
        scored = []
        for s in songs:
            name = s.get('name', '').lower()
            arts = s.get('artists', [])
            aname = arts[0].get('name', '').lower() if arts else ''
            score = 0
            if sl in name or name in sl:
                score += 10
            if al and (al in aname or aname in al):
                score += 5
            scored.append((score, s))
        scored.sort(key=lambda x: -x[0])
        return scored[0][1] if scored and scored[0][0] > 0 else (songs[0] if songs else None)

    @staticmethod
    def _clean_lrc(text):
        text = re.sub(r'\\[\\d{2}:\\d{2}\\.\\d{2}\\]', '', text)
        text = re.sub(r'\\[\\d+:\\d+\\.\\d+\\]', '', text)
        text = re.sub(r'\\[(ti|ar|al|by|offset):[^\\]]*\\]', '', text)
        text = re.sub(r'\\[(Verse|Chorus|Intro|Outro|Bridge|Hook)\\]', '', text)
        lines = [l.strip() for l in text.split(chr(10)) if l.strip()]
        return chr(10).join(lines)

    async def get_album_tracks(self, artist, album):
        return []