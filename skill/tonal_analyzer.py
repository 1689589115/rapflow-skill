"""
声调搭配分析模块 - v1.5.0
分析中文说唱歌词的抑扬顿挫感，识别声调模式并给出质量建议
"""

import math
from typing import Dict, List, Optional
from collections import Counter

from pypinyin import pinyin, Style


# 升调转移：1→2, 2→3, 3→4
_RISING_TRANSITIONS = {(1, 2), (2, 3), (3, 4)}
# 降调转移：4→3, 3→2, 2→1
_FALLING_TRANSITIONS = {(4, 3), (3, 2), (2, 1)}
# 最大香农熵（5个不同声调均匀分布）
_MAX_ENTROPY = math.log2(5)


def _get_char_tone(char: str) -> int:
    """
    获取单个汉字的声调

    Args:
        char: 单个字符

    Returns:
        声调数字（1-4）或 0（轻声）或 -1（非汉字）
    """
    if not ('一' <= char <= '龥'):
        return -1

    try:
        result = pinyin(char, style=Style.TONE3, strict=False)
        if not result or not result[0]:
            return -1
        # TONE3 格式如 'tian1'，最后一位是声调数字
        tone_str = result[0][0][-1]
        if tone_str.isdigit():
            return int(tone_str)
        return 0  # 轻声
    except Exception:
        return -1


def _extract_tone_sequence(line: str) -> List[int]:
    """
    提取一行的声调序列

    Args:
        line: 歌词行文本

    Returns:
        声调列表，非汉字位置为 -1
    """
    return [_get_char_tone(c) for c in line]


def _shannon_entropy(tones: List[int]) -> float:
    """
    计算声调序列的香农熵

    Args:
        tones: 声调列表（过滤掉 -1）

    Returns:
        香农熵值，范围 [0, log2(5)]
    """
    # 过滤非汉字
    valid_tones = [t for t in tones if t != -1]
    if not valid_tones:
        return 0.0

    counter = Counter(valid_tones)
    total = len(valid_tones)
    entropy = 0.0
    for count in counter.values():
        prob = count / total
        if prob > 0:
            entropy -= prob * math.log2(prob)
    return round(entropy, 4)


def _classify_pattern(tones: List[int]) -> str:
    """
    判定声调模式类型

    Args:
        tones: 声调序列

    Returns:
        'flat' / 'alternating' / 'wave'
    """
    # 过滤非汉字
    valid = [t for t in tones if t != -1]
    if len(valid) < 2:
        return "wave"

    # 同调比例：相邻两字声调相同的比例
    same_count = sum(
        1 for i in range(1, len(valid)) if valid[i] == valid[i - 1]
    )
    same_ratio = same_count / (len(valid) - 1)

    # 交替比例：相邻两字声调不同的比例
    diff_ratio = 1.0 - same_ratio

    if diff_ratio >= 0.65:
        return "alternating"
    elif same_ratio >= 0.70:
        return "flat"
    else:
        return "wave"


def _calc_transition_ratios(tones: List[int]) -> tuple:
    """
    计算升调和降调转移比例

    Args:
        tones: 声调序列

    Returns:
        (rising_ratio, falling_ratio)
    """
    valid = [t for t in tones if t != -1]
    if len(valid) < 2:
        return 0.0, 0.0

    transitions = [(valid[i - 1], valid[i]) for i in range(1, len(valid))]
    total = len(transitions)

    rising = sum(1 for t in transitions if t in _RISING_TRANSITIONS)
    falling = sum(1 for t in transitions if t in _FALLING_TRANSITIONS)

    return rising / total, falling / total


def _analyze_line(line: str, line_index: int) -> Dict:
    """分析单行歌词的声调特征"""
    tone_seq = _extract_tone_sequence(line)
    pattern = _classify_pattern(tone_seq)
    entropy = _shannon_entropy(tone_seq)
    rising, falling = _calc_transition_ratios(tone_seq)

    return {
        "line_index": line_index,
        "tone_sequence": tone_seq,
        "pattern_type": pattern,
        "tonal_entropy": entropy,
        "rising_ratio": round(rising, 4),
        "falling_ratio": round(falling, 4),
    }


def _generate_feedback(lines_data: List[Dict]) -> List[str]:
    """
    生成自然语言质量评估建议

    Args:
        lines_data: _analyze_line 返回列表

    Returns:
        建议列表
    """
    feedback = []

    for item in lines_data:
        idx = item["line_index"] + 1
        tone_seq = item["tone_sequence"]
        pattern = item["pattern_type"]
        entropy = item["tonal_entropy"]
        rising = item["rising_ratio"]
        falling = item["falling_ratio"]

        # 过滤非汉字
        valid_tones = [t for t in tone_seq if t != -1]
        if not valid_tones:
            continue

        # 单调分析
        if pattern == "flat":
            tone_counts = Counter(valid_tones)
            most_common = tone_counts.most_common(1)[0]
            tone_name = {1: "阴平（一声）", 2: "阳平（二声）",
                         3: "上声（三声）", 4: "去声（四声）"}.get(most_common[0], str(most_common[0]))
            pct = most_common[1] / len(valid_tones) * 100
            feedback.append(
                f"第{idx}句声调过于单一（{tone_name}占比{pct:.0f}%），"
                f"读音平淡，建议加入其他声调增强起伏感"
            )

        # 熵过低
        if entropy < 0.5 and len(valid_tones) >= 4:
            feedback.append(
                f"第{idx}句声调多样性不足（熵={entropy:.2f}），"
                f"建议增加声调变化以提升抑扬顿挫感"
            )

        # 升降调严重失衡
        if rising < 0.05 and falling > 0.3 and len(valid_tones) >= 5:
            feedback.append(
                f"第{idx}句降调过多（降调比例{falling:.0%}），整体过于下沉，"
                f"建议适当加入升调增强节奏感"
            )
        elif falling < 0.05 and rising > 0.3 and len(valid_tones) >= 5:
            feedback.append(
                f"第{idx}句升调过多（升调比例{rising:.0%}），整体过于上扬，"
                f"建议适当加入降调增加力度感"
            )

    # 整体建议
    if lines_data:
        avg_entropy = sum(d["tonal_entropy"] for d in lines_data) / len(lines_data)
        if avg_entropy > 1.8:
            feedback.append("整体声调搭配丰富，抑扬顿挫感强，继续保持")
        elif avg_entropy < 0.8:
            feedback.append("整体声调较为单调，建议增加声调变化以提升歌曲节奏感")

    return feedback


def analyse_lyric_tones(lines: List[str]) -> Dict:
    """
    分析整段歌词的声调搭配

    Args:
        lines: 歌词行列表

    Returns:
        dict with lines, stats, feedback
    """
    if not lines:
        return {
            "lines": [],
            "stats": {
                "avg_entropy": 0.0,
                "dominant_pattern": "N/A",
                "overall_fluidity_score": 0.0,
            },
            "feedback": ["无歌词可分析"],
        }

    # 逐行分析
    lines_data = [_analyze_line(line, i) for i, line in enumerate(lines)]

    # 段落级聚合
    valid_entropies = [d["tonal_entropy"] for d in lines_data]
    avg_entropy = sum(valid_entropies) / len(valid_entropies) if valid_entropies else 0.0

    # 主导模式
    pattern_counter = Counter(d["pattern_type"] for d in lines_data)
    dominant_pattern = pattern_counter.most_common(1)[0][0] if pattern_counter else "wave"

    # 综合流畅度评分
    # fluidity = (avg_alternating_rate * 50) + (normalized_avg_entropy * 50)
    alternating_rate = sum(
        1 for d in lines_data if d["pattern_type"] == "alternating"
    ) / len(lines_data) if lines_data else 0.0
    normalized_entropy = avg_entropy / _MAX_ENTROPY if _MAX_ENTROPY > 0 else 0.0
    fluidity_score = round(
        alternating_rate * 50 + normalized_entropy * 50, 1
    )
    fluidity_score = max(0.0, min(100.0, fluidity_score))

    stats = {
        "avg_entropy": round(avg_entropy, 4),
        "dominant_pattern": dominant_pattern,
        "overall_fluidity_score": fluidity_score,
    }

    feedback = _generate_feedback(lines_data)

    return {
        "lines": lines_data,
        "stats": stats,
        "feedback": feedback,
    }
