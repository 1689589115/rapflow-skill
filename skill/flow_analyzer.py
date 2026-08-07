"""
Flow 节奏分析模块 - v1.5.0
分析说唱歌词的节奏特征，识别 Boom Bap、Trap、Drill、Chopper 等风格
"""

from typing import Dict, List, Optional
from collections import Counter


# Flow 风格特征规则
FLOW_RULES = {
    "Boom Bap": {
        "description": "经典90年代嘻哈风格，稳定四拍节奏",
        "indicators": {
            "steady_beat": 0.3,      # 稳定的段落节奏
            "syllable_range": (8, 14),  # 中等音节密度
            "rhyme_density_min": 0.2,
        }
    },
    "Trap": {
        "description": "南方嘻哈风格，快速三连音、重复flow",
        "indicators": {
            "repetitive_pattern": 0.4,  # 高重复性
            "syllable_range": (6, 12),
            "rhyme_density_min": 0.3,
        }
    },
    "Drill": {
        "description": "阴暗风格，不规则节奏、停顿",
        "indicators": {
            "irregular_pattern": 0.3,   # 不规则性
            "syllable_range": (5, 10),
            "rhyme_density_min": 0.15,
        }
    },
    "Chopper": {
        "description": "快速连续flow，高密度音节",
        "indicators": {
            "high_density": 0.5,        # 高密度
            "syllable_range": (14, 25),
            "rhyme_density_min": 0.4,
        }
    },
    "Melodic": {
        "description": "旋律说唱，抒情flow",
        "indicators": {
            "melodic_pattern": 0.3,     # 旋律性
            "syllable_range": (10, 18),
            "rhyme_density_min": 0.25,
        }
    },
}


def _count_chinese_syllables(text: str) -> int:
    """统计中文音节数（汉字+英文单词）"""
    chinese = sum(1 for c in text if '一' <= c <= '龥')
    english_words = len(text.split()) - sum(1 for w in text.split() if w and '一' <= w[0] <= '龥')
    return chinese + max(english_words, 0)


def _analyze_line_patterns(lines: List[str]) -> Dict:
    """分析各行的节奏模式"""
    line_stats = []
    for line in lines:
        syllables = _count_chinese_syllables(line)
        chinese_count = sum(1 for c in line if '一' <= c <= '龥')
        line_stats.append({
            "syllables": syllables,
            "chinese_chars": chinese_count,
            "length": len(line),
        })
    return line_stats


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

    line_stats = _analyze_line_patterns(lines)
    avg_syllables = sum(s["syllables"] for s in line_stats) / len(line_stats)
    avg_density = sum(rhyme_densities) / len(rhyme_densities)

    # 计算重复性（Trap 特征）
    syllable_patterns = [s["syllables"] for s in line_stats]
    pattern_counter = Counter(syllable_patterns)
    most_common_pattern_count = pattern_counter.most_common(1)[0][1] if pattern_counter else 0
    repetition_score = most_common_pattern_count / len(lines) if lines else 0

    # 计算不规则性（Drill 特征）
    if len(line_stats) > 1:
        syllable_diffs = [
            abs(line_stats[i]["syllables"] - line_stats[i-1]["syllables"])
            for i in range(1, len(line_stats))
        ]
        irregularity_score = sum(1 for d in syllable_diffs if d >= 4) / len(syllable_diffs) if syllable_diffs else 0
    else:
        irregularity_score = 0.0

    # 匹配 Flow 风格
    scores = {}
    for style, rules in FLOW_RULES.items():
        indicators = rules["indicators"]
        score = 0.0
        total_weight = 0.0

        # 音节密度匹配
        syl_range = indicators.get("syllable_range", (0, 100))
        if syl_range[0] <= avg_syllables <= syl_range[1]:
            score += 0.3
        total_weight += 0.3

        # 押韵密度匹配
        min_density = indicators.get("rhyme_density_min", 0)
        if avg_density >= min_density:
            score += 0.2
        total_weight += 0.2

        # 风格特定指标
        if style == "Trap" and indicators.get("repetitive_pattern", 0):
            if repetition_score >= 0.3:
                score += indicators["repetitive_pattern"]
            total_weight += indicators["repetitive_pattern"]

        if style == "Drill" and indicators.get("irregular_pattern", 0):
            if irregularity_score >= 0.3:
                score += indicators["irregular_pattern"]
            total_weight += indicators["irregular_pattern"]

        if style == "Chopper" and indicators.get("high_density", 0):
            if avg_syllables >= 14:
                score += indicators["high_density"]
            total_weight += indicators["high_density"]

        if total_weight > 0:
            scores[style] = score / total_weight

    # 确定最佳风格
    if not scores:
        return {
            "style": "Boom Bap",
            "confidence": 0.5,
            "characteristics": {
                "avg_syllables": round(avg_syllables, 1),
                "avg_rhyme_density": round(avg_density, 3),
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
        "style_scores": {k: round(v, 2) for k, v in scores.items()},
    }

    details = (
        f"{best_style}风格 ({FLOW_RULES[best_style]['description']})，"
        f"平均音节数{avg_syllables:.1f}，押韵密度{avg_density:.2f}，"
        f"置信度{confidence:.0%}"
    )

    return {
        "style": best_style,
        "confidence": confidence,
        "characteristics": characteristics,
        "details": details,
    }
