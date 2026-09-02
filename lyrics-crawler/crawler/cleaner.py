"""歌词清洗模块。
提供一系列管道函数，将原始歌词（可能包含 LRC 时间戳、广告语、
平台水印、多余空行）清洗为干净的纯文本歌词。
"""

from __future__ import annotations

import re
from typing import Dict


# ---------------------------------------------------------------------------
# 各清洗步骤
# ---------------------------------------------------------------------------

# LRC 时间戳正则：匹配 [mm:ss.xx] 或 [mm:ss]
_RE_TIMESTAMP = re.compile(r"\[\d{1,2}:\d{2}(?:\.\d{2})?\]")

# 常见广告/水印短语（大小写不敏感）
_AD_PATTERNS: list[str] = [
    r"^Produced\b.*$",
    r"^Produced\s+and\s+engineered\b.*$",
    r"^Recorded\s+at\b.*$",
    r"^Mixed\s+by\b.*$",
    r"^Written\s+by\b.*$",
    r"^Lyrics\s+powered\s+by\b.*$",
    r"^Lyrics\s+source:\s*.*$",
    r"\[Advertisement\]",
    r"聽歌不收費·網易雲音樂",
    r"网易云音乐",
    r"Lyrics provided by Genius",
    r"View this Song on Genius",
]
_RE_ADS = re.compile("|".join(_AD_PATTERNS), re.IGNORECASE)

# 方括号标签行：整行为 [xxx] 且长度 < 40 字符，视为标签而非歌词
_RE_BRACKET_TAG = re.compile(r"^\[[^\[\]]{1,39}\]$\s*$", re.MULTILINE)

# 连续空行合并：将连续 3 个及以上空行合并为 2 个
_RE_MULTIPLE_BLANK = re.compile(r"\n{3,}")

# 段落标记正则：支持中英文段标
# 英文：[Verse] [Hook] [Chorus] [Bridge] [Intro] [Outro] [Pre-Chorus]
# 中文：[主歌] [副歌] [说唱] [合唱] [桥段] [前奏] [尾奏]
_RE_SECTION = re.compile(
    r"\[(?:Verse|Hook|Chorus|Bridge|Intro|Outro|Pre[- ]?Chorus|Cop[ae]tta|Drop|Post[- ]?Drop|"
    r"主歌|副歌|说唱|合唱|桥段|前奏|尾奏|间奏|独白|Rap)\]",
    re.IGNORECASE,
)


def remove_timestamp(text: str) -> str:
    """去掉 LRC 时间戳标记，如 [00:12.34]、[1:23]。
    直接替换为空字符串，保留歌词正文。
    """
    return _RE_TIMESTAMP.sub("", text)


def remove_ads_and_platform_watermark(text: str) -> str:
    """移除广告、工程信息、平台水印等无关行。
    规则：
    - 先剥离时间戳再匹配已知广告短语（因为广告行可能带 [mm:ss] 前缀）
    - 纯方括号包裹且长度 < 40 的行视为标签行，删除
    """
    lines = text.splitlines()
    kept: list[str] = []
    for line in lines:
        stripped = _RE_TIMESTAMP.sub("", line.strip())
        if not stripped:
            kept.append(line)
            continue
        # 检查已知广告/水印短语（时间戳已剥离）
        if _RE_ADS.search(stripped):
            continue
        # 检查方括号标签行
        if _RE_BRACKET_TAG.match(line.strip()):
            continue
        kept.append(line)
    return "\n".join(kept)


def remove_empty_lines(text: str) -> str:
    """将连续超过两行的空行合并为单一换行，去除首尾空白。
    例如连续 5 个空行 → 1 个空行（即一个换行符），
    使歌词结构更紧凑。
    """
    result = _RE_MULTIPLE_BLANK.sub("\n\n", text)
    return result.strip()


def clean_lyrics(raw_text: str) -> str:
    """总清洗管道：时间戳 → 广告/水印 → 空行合并 → strip 收尾。
    按顺序调用各清洗步骤，确保输出为干净的纯文本歌词。
    """
    text = remove_timestamp(raw_text)
    text = remove_ads_and_platform_watermark(text)
    text = remove_empty_lines(text)
    return text.strip()


def split_sections(cleaned_text: str) -> Dict[str, str]:
    """根据段标（[Verse]、[Hook]、[Chorus] 等）拆分歌词。
    返回 {"verse": "...", "hook": "...", ...} 字典。
    所有没有明确段标的行统一归入 "main" 键。
    段标名转为小写作字典键。
    """
    sections: dict[str, str] = {}
    current_key: str = "main"
    current_lines: list[str] = []

    for line in cleaned_text.splitlines():
        stripped = line.strip()
        # 检查是否是段标行
        m = _RE_SECTION.search(stripped)
        if m is not None:
            # 先保存上一段
            if current_lines:
                sections[current_key] = "\n".join(current_lines).strip()
                current_lines = []
            # 新段：取段标名（不含方括号）
            section_name = m.group(0).strip("[]").lower()
            # 映射常见别名
            section_name = _normalize_section_name(section_name)
            current_key = section_name
            continue
        current_lines.append(line)

    # 保存最后一段
    if current_lines:
        sections[current_key] = "\n".join(current_lines).strip()

    return sections


def _normalize_section_name(name: str) -> str:
    """将段标名统一为规范化键名。"""
    # 统一转为小写后再查表，避免大小写不匹配
    name_lower = name.lower()
    mapping: dict[str, str] = {
        "verse": "verse",
        "hook": "hook",
        "chorus": "chorus",
        "bridge": "bridge",
        "intro": "intro",
        "outro": "outro",
        "pre-chorus": "pre-chorus",
        "copetta": "intro",
        "drop": "drop",
        "post-drop": "outro",
        "主歌": "verse",
        "副歌": "chorus",
        "说唱": "verse",
        "合唱": "chorus",
        "桥段": "bridge",
        "前奏": "intro",
        "尾奏": "outro",
        "间奏": "intro",
        "独白": "verse",
        "rap": "verse",
    }
    return mapping.get(name_lower, name_lower)
