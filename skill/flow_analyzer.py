"""
Flow 节奏分析模块 - v1.5.0
分析说唱歌词的节奏特征，识别 Boom Bap、Trap、Drill、Chopper 等风格
"""

from typing import Dict, List
from collections import Counter


def _count_chinese_syllables(text: str) -> int:
    """统计中文音节数（汉字+英文单词）"""
    chinese = sum(1 for c in text if '一' <= c <= '龥')
    english_words = len(text.split()) - sum(
        1 for w in text.split() if w and '一' <= w[0] <= '龥'
    )
    return chinese + max(english_words, 0)


def analyze_flow(
    lines: List[str],
    rhyme_densities: List[float],
) -> Dict:
    """
    分析说唱歌词的 Flow 风格

    Args:
        lines: 歌词行列表
        rhyme_densities: 每行的押韵密度列表

    Returns:
        dict with style, confidence, characteristics
    """
    if not lines or not rhyme_densities:
        return {
            "style": "Unknown",
            "confidence": 0.0,
            "characteristics": {},
            "details": "无法分析：输入为空"
        }

    syllable_counts = [_count_chinese_syllables(l) for l in lines]
    avg_syllables = sum(syllable_counts) / len(syllable_counts)
    avg_density = sum(rhyme_densities) / len(rhyme_densities)

    # 计算重复性（Trap 特征）
    pattern_counter = Counter(syllable_counts)
    most_common_count = pattern_counter.most_common(1)[0][1]
    repetition_score = most_common_count / len(lines)

    # 计算不规则性（Drill 特征）
    if len(syllable_counts) > 1:
        diffs = [
            abs(syllable_counts[i] - syllable_counts[i-1])
            for i in range(1, len(syllable_counts))
        ]
        irregularity_score = sum(1 for d in diffs if d >= 4) / len(diffs)
    else:
        irregularity_score = 0.0

    # 正交评分：每个维度独立计算，避免区间重叠干扰
    scores = {}

    # Boom Bap: 中等音节(8-14) + 中等密度(0.2-0.6) + 低重复
    bb_score = 0.0
    if 8 <= avg_syllables <= 14:
        bb_score += 0.35
    if 0.2 <= avg_density <= 0.6:
        bb_score += 0.35
    if repetition_score < 0.5:
        bb_score += 0.3
    if bb_score > 0:
        scores["Boom Bap"] = round(bb_score, 2)

    # Trap: 重复性高 + 较低音节(6-11)
    trap_score = 0.0
    if 6 <= avg_syllables <= 11:
        trap_score += 0.3
    if 0.3 <= avg_density <= 0.6:
        trap_score += 0.2
    if repetition_score >= 0.3:
        trap_score += 0.5
    if trap_score > 0:
        scores["Trap"] = round(trap_score, 2)

    # Drill: 不规则性高 + 低中音节(5-10)
    drill_score = 0.0
    if 5 <= avg_syllables <= 10:
        drill_score += 0.3
    if 0.15 <= avg_density <= 0.5:
        drill_score += 0.2
    if irregularity_score >= 0.3:
        drill_score += 0.5
    if drill_score > 0:
        scores["Drill"] = round(drill_score, 2)

    # Chopper: 高音节(14+) + 高密度(0.4+)
    chopper_score = 0.0
    if avg_syllables >= 14:
        chopper_score += 0.5
    elif avg_syllables >= 12:
        chopper_score += 0.3
    if avg_density >= 0.4:
        chopper_score += 0.5
    if chopper_score > 0:
        scores["Chopper"] = round(chopper_score, 2)

    # Melodic: 中高音节(10-16) + 中密度(0.25-0.5)
    melodic_score = 0.0
    if 10 <= avg_syllables <= 16:
        melodic_score += 0.4
    if 0.25 <= avg_density <= 0.5:
        melodic_score += 0.4
    if repetition_score < 0.5:
        melodic_score += 0.2
    if melodic_score > 0:
        scores["Melodic"] = round(melodic_score, 2)

    # 确定最佳风格
    if not scores:
        return {
            "style": "Boom Bap",
            "confidence": 0.5,
            "characteristics": {
                "avg_syllables": round(avg_syllables, 1),
                "avg_rhyme_density": round(avg_density, 3),
                "repetition_score": round(repetition_score, 2),
                "irregularity_score": round(irregularity_score, 2),
            },
            "details": "标准说唱风格"
        }

    best_style = max(scores, key=scores.get)
    confidence = round(scores[best_style], 2)

    characteristics = {
        "avg_syllables_per_line": round(avg_syllables, 1),
        "avg_rhyme_density": round(avg_density, 3),
        "repetition_score": round(repetition_score, 2),
        "irregularity_score": round(irregularity_score, 2),
        "style_scores": scores,
    }

    style_desc = {
        "Boom Bap": "经典90年代嘻哈风格，稳定四拍节奏",
        "Trap": "南方嘻哈风格，快速三连音、重复flow",
        "Drill": "阴暗风格，不规则节奏、停顿",
        "Chopper": "快速连续flow，高密度音节",
        "Melodic": "旋律说唱，抒情flow",
    }

    details = (
        f"{best_style}风格 ({style_desc[best_style]})，"
        f"平均音节数{avg_syllables:.1f}，押韵密度{avg_density:.2f}，"
        f"置信度{confidence:.0%}"
    )

    return {
        "style": best_style,
        "confidence": confidence,
        "characteristics": characteristics,
        "details": details,
    }
