"""基于 0xHJK/music-dl 的多源歌词搜索。

支持网易云音乐和酷狗音乐，通过搜索歌曲找到正确的歌曲ID，然后拉取歌词。
解决 lrc.cx API 不支持 song 参数的缺陷。
"""

from __future__ import annotations

import base64
import binascii
import copy
import json
import logging
import re
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ── 网易云加密工具类（来自 0xHJK/music-dl/netease.py）─────────────

class _NeteaseApi:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "referer": "http://music.163.com/",
    })
    _AES_KEY = binascii.unhexlify("7246674226682325323F5E6544673A51")
    _NONCE = b"0CoJUm6Qyw8W8jud"
    _PUBKEY = "010001"
    _MODULUS = (
        "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7"
        "b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280"
        "104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932"
        "575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b"
        "3ece0462db0a22b8e7"
    )

    @classmethod
    def _aes(cls, text: str, key: bytes) -> bytes:
        from Crypto.Cipher import AES
        pad = 16 - len(text) % 16
        text += chr(pad) * pad
        encryptor = AES.new(key, AES.MODE_ECB)
        return encryptor.encrypt(text.encode("utf-8"))

    @classmethod
    def encode_netease_data(cls, data: dict) -> str:
        """网易云 API 参数编码（简化版）。"""
        raw = json.dumps(data)
        key = cls._AES_KEY
        from Crypto.Cipher import AES
        encryptor = AES.new(key, AES.MODE_ECB)
        pad = 16 - len(raw) % 16
        raw += chr(pad) * pad
        return binascii.hexlify(encryptor.encrypt(raw.encode("utf-8"))).upper().decode()

    @classmethod
    def _aes_full(cls, text: bytes, key: bytes, iv: bytes) -> bytes:
        from Crypto.Cipher import AES
        pad = 16 - len(text) % 16
        text += bytes([pad] * pad)
        encryptor = AES.new(key, AES.MODE_CBC, iv)
        return encryptor.encrypt(text)

    @classmethod
    def _rsa(cls, text: str, pubkey: str, modulus: str) -> str:
        text = text[::-1]
        rs = pow(int(binascii.hexlify(text.encode("utf-8")), 16),
                 int(pubkey, 16), int(modulus, 16))
        return format(rs, "x").zfill(256)

    @classmethod
    def _create_key(cls, size: int = 16) -> bytes:
        return binascii.hexlify(__import__("os").urandom(size))[:16].decode()

    @classmethod
    def encrypted_request(cls, data: dict) -> dict:
        """网易云完整加密请求参数。"""
        data_bytes = json.dumps(data).encode("utf-8")
        secret = cls._create_key(16)
        params = base64.b64encode(
            cls._aes_full(data_bytes, cls._NONCE, b"0102030405060708")
        )
        enc_params = base64.b64encode(
            cls._aes_full(params, secret, b"0102030405060708")
        )
        enc_seckey = cls._rsa(secret.decode(), cls._PUBKEY, cls._MODULUS)
        return {"params": enc_params.decode(), "encSecKey": enc_seckey}


# ── 歌词源实现 ─────────────────────────────────────────────────────

class MusicDlSource:
    """基于 0xHJK/music-dl 的多源歌词搜索（网易云 + 酷狗）。"""

    NAME = "music_dl"

    def search_lyrics(self, artist: str, song: str) -> Optional[dict]:
        """搜索歌词，依次尝试网易云和酷狗。"""
        # 构造搜索关键词：歌手 + 歌名
        keyword = f"{artist} {song}"

        # 1. 尝试网易云
        result = self._search_netease(artist, song, keyword)
        if result:
            logger.info("Found lyrics via netease: %s - %s", artist, song)
            return result

        # 2. 尝试酷狗
        result = self._search_kugou(artist, song, keyword)
        if result:
            logger.info("Found lyrics via kugou: %s - %s", artist, song)
            return result

        logger.info("No lyrics found for '%s - %s'", artist, song)
        return None

    def _search_netease(self, artist: str, song: str, keyword: str) -> Optional[dict]:
        """网易云搜索 + 歌词拉取。"""
        try:
            # 搜索歌曲
            eparams = {
                "method": "POST",
                "url": "http://music.163.com/api/cloudsearch/pc",
                "params": {"s": keyword, "type": 1, "offset": 0, "limit": 5},
            }
            data = {"eparams": _NeteaseApi.encode_netease_data(eparams)}
            resp = _NeteaseApi.session.post(
                "http://music.163.com/api/linux/forward",
                data=data, timeout=8,
            )
            resp.raise_for_status()
            songs = resp.json().get("result", {}).get("songs", [])

            # 找最匹配的（优先匹配歌名和歌手）
            target = self._find_best_match(songs, artist, song)
            if not target:
                return None

            song_id = target.get("id")
            # 拉取歌词
            lyrics = self._fetch_netease_lyrics(song_id)
            if not lyrics:
                return None

            return {
                "artist": target.get("artist", artist),
                "song": target.get("song", song),
                "lyrics": lyrics,
                "raw_lyrics": lyrics,
                "url": f"https://music.163.com/#/song?id={song_id}",
                "album": target.get("album", ""),
                "release_date": "",
                "source": "netease",
                "confidence": 0.95,
            }
        except Exception as e:
            logger.warning("Netease search failed for '%s - %s': %r", artist, song, e)
            return None

    def _fetch_netease_lyrics(self, song_id: int) -> str:
        """从网易云拉取歌词。"""
        try:
            from Crypto.Cipher import AES
            import os as _os
            row_data = {"csrf_token": "", "id": song_id, "lv": -1, "tv": -1}
            data_bytes = json.dumps(row_data).encode("utf-8")
            secret = _NeteaseApi._create_key(16)
            params = base64.b64encode(
                _NeteaseApi._aes_full(data_bytes, _NeteaseApi._NONCE, b"0102030405060708")
            )
            enc_params = base64.b64encode(
                _NeteaseApi._aes_full(params, secret.encode(), b"0102030405060708")
            )
            enc_seckey = _NeteaseApi._rsa(secret, _NeteaseApi._PUBKEY, _NeteaseApi._MODULUS)
            resp = _NeteaseApi.session.post(
                "https://music.163.com/weapi/song/lyric",
                data={"params": enc_params.decode(), "encSecKey": enc_seckey},
                timeout=8,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("lrc", {}).get("lyric", "")
        except Exception as e:
            logger.warning("Netease lyrics fetch failed for id=%s: %r", song_id, e)
            return ""

    def _search_kugou(self, artist: str, song: str, keyword: str) -> Optional[dict]:
        """酷狗搜索 + 歌词拉取。"""
        try:
            resp = requests.get(
                "http://songsearch.kugou.com/song_search_v2",
                params={"keyword": keyword, "platform": "WebFilter",
                        "format": "json", "page": 1, "pagesize": 5},
                headers={"Referer": "http://www.kugou.com",
                         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                timeout=8,
            )
            resp.raise_for_status()
            songs = resp.json().get("data", {}).get("lists", [])

            target = self._find_best_match(songs, artist, song, is_kugou=True)
            if not target:
                return None

            song_hash = target.get("FileHash")
            if not song_hash:
                return None

            # 从酷狗拉取歌词
            lyrics = self._fetch_kugou_lyrics(song_hash)
            if not lyrics:
                return None

            return {
                "artist": target.get("SingerName", artist),
                "song": target.get("SongName", song),
                "lyrics": lyrics,
                "raw_lyrics": lyrics,
                "url": f"https://www.kugou.com/",
                "album": target.get("AlbumName", ""),
                "release_date": "",
                "source": "kugou",
                "confidence": 0.9,
            }
        except Exception as e:
            logger.warning("Kugou search failed for '%s - %s': %r", artist, song, e)
            return None

    def _fetch_kugou_lyrics(self, song_hash: str) -> str:
        """从酷狗拉取歌词。"""
        try:
            resp = requests.get(
                f"http://krcs.kugou.com/search?ver=1&client=mobi&hash={song_hash}&album_audio_id=",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=8,
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("candidates"):
                return ""
            candidate = data["candidates"][0]
            id_val = candidate.get("id")
            accesskey = candidate.get("accesskey")
            if not id_val or not accesskey:
                return ""
            lrc_resp = requests.get(
                f"http://lyrics.kugou.com/download?ver=1&client=pc&id={id_val}&accesskey={accesskey}&fmt=lrc&charset=utf8",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=8,
            )
            lrc_resp.raise_for_status()
            lrc_data = lrc_resp.json()
            raw = lrc_data.get("content", "")
            return base64.b64decode(raw).decode("utf-8")
        except Exception as e:
            logger.warning("Kugou lyrics fetch failed for hash=%s: %r", song_hash, e)
            return ""

    @staticmethod
    def _find_best_match(songs: list, artist: str, song: str, is_kugou: bool = False) -> Optional[dict]:
        """从搜索结果中找最匹配的歌曲。"""
        artist_lower = artist.lower().strip()
        song_lower = song.lower().strip()
        best = None
        best_score = -1

        for item in songs:
            if is_kugou:
                item_artist = item.get("SingerName", "").lower()
                item_song = item.get("SongName", "").lower()
            else:
                item_artist = " ".join(s.get("name", "").lower() for s in item.get("ar", [])).strip()
                item_song = item.get("name", "").lower()

            score = 0
            # 歌名精确匹配
            if song_lower in item_song or item_song in song_lower:
                score += 10
            # 歌手匹配
            if artist_lower and (artist_lower in item_artist or item_artist in artist_lower):
                score += 5
            # 去重：包含空格和特殊字符的模糊匹配
            if re.sub(r'[\s\W_]+', '', song_lower) in re.sub(r'[\s\W_]+', '', item_song):
                score += 3

            if score > best_score:
                best_score = score
                best = item

        # 必须有一定匹配度才返回
        if best and best_score >= 5:
            return best
        return None
