"""Profile Builder — MC风格蒸馏。

基于三路分析结果，生成说唱歌手的风格档案（Profile）。
包含：押韵风格、Flow特征、声调特点、综合评分等。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ProfileBuilder:
    """说唱歌手风格档案生成器。"""

    def __init__(self) -> None:
        pass

    def build(
        self,
        artist: str,
        song: str,
        analysis_result: dict,
    ) -> dict:
        """生成歌手风格档案。

        参数：
            artist: 歌手名
            song: 歌名
            analysis_result: 三路分析结果

        返回：
            Profile dict
        """
        profile = {
            "meta": {
                "artist": artist,
                "song": song,
                "generated_at": datetime.now().isoformat(),
                "version": "1.0.0",
            },
            "rhyme_profile": self._build_rhyme_profile(analysis_result.get("rhyme", {})),
            "flow_profile": self._build_flow_profile(analysis_result.get("flow", {})),
            "tonal_profile": self._build_tonal_profile(analysis_result.get("tonal", {})),
            "overall_score": self._calculate_overall_score(analysis_result),
            "style_tags": self._extract_style_tags(analysis_result),
        }

        return profile

    def _build_rhyme_profile(self, rhyme_info: dict) -> dict:
        """构建押韵档案。"""
        density = rhyme_info.get("rhyme_density", 0)
        complex_count = rhyme_info.get("complex_rhymes", 0)
        total_lines = rhyme_info.get("total_lines", 1)

        # 判断押韵风格
        if density >= 0.8 and complex_count > total_lines * 0.5:
            rhyme_style = "Complex Multi-Rhyme"
            rhyme_score = 9.0
        elif density >= 0.6:
            rhyme_style = "Balanced"
            rhyme_score = 7.5
        else:
            rhyme_style = "Simple"
            rhyme_score = 6.0

        return {
            "style": rhyme_style,
            "density": round(density, 2),
            "complex_rhyme_ratio": round(complex_count / max(total_lines, 1), 2),
            "score": rhyme_score,
        }

    def _build_flow_profile(self, flow_info: dict) -> dict:
        """构建 Flow 档案。"""
        style = flow_info.get("style", "Unknown")
        confidence = flow_info.get("confidence", 0)

        # Flow 风格描述
        style_descriptions = {
            "Boom Bap": "经典90年代嘻哈风格，稳定四拍节奏",
            "Trap": "南方嘻哈风格，快速三连音、重复flow",
            "Drill": "阴暗风格，不规则节奏、停顿",
            "Chopper": "快速连续flow，高密度音节",
            "Melodic": "旋律说唱，抒情flow",
        }

        return {
            "style": style,
            "confidence": confidence,
            "description": style_descriptions.get(style, "未知风格"),
            "score": round(confidence * 10, 1),
        }

    def _build_tonal_profile(self, tonal_info: dict) -> dict:
        """构建声调档案。"""
        match_rate = tonal_info.get("tonal_match_rate", 0)
        rhythm_score = tonal_info.get("rhythm_score", 0)
        dominant_pattern = tonal_info.get("dominant_pattern", "N/A")

        # 判断声调质量
        if match_rate >= 0.8:
            tonal_quality = "Excellent"
            tonal_score = 9.0
        elif match_rate >= 0.6:
            tonal_quality = "Good"
            tonal_score = 7.5
        else:
            tonal_quality = "Fair"
            tonal_score = 6.0

        return {
            "quality": tonal_quality,
            "match_rate": round(match_rate, 2),
            "rhythm_score": round(rhythm_score, 1),
            "dominant_pattern": dominant_pattern,
            "score": tonal_score,
        }

    def _calculate_overall_score(self, analysis_result: dict) -> dict:
        """计算综合评分。"""
        rhyme_score = analysis_result.get("rhyme", {}).get("score", 7.0)
        flow_score = analysis_result.get("flow", {}).get("score", 7.0)
        tonal_score = analysis_result.get("tonal", {}).get("score", 7.0)

        # 加权平均
        overall = rhyme_score * 0.4 + flow_score * 0.35 + tonal_score * 0.25

        return {
            "rhyme": round(rhyme_score, 1),
            "flow": round(flow_score, 1),
            "tonal": round(tonal_score, 1),
            "overall": round(overall, 1),
        }

    def _extract_style_tags(self, analysis_result: dict) -> list:
        """提取风格标签。"""
        tags = []

        # 押韵标签
        rhyme_density = analysis_result.get("rhyme", {}).get("rhyme_density", 0)
        if rhyme_density >= 0.8:
            tags.append("高密度押韵")
        elif rhyme_density >= 0.6:
            tags.append("中等押韵")

        # Flow 标签
        flow_style = analysis_result.get("flow", {}).get("style", "")
        if flow_style:
            tags.append(f"{flow_style}Flow")

        # 声调标签
        tonal_quality = analysis_result.get("tonal", {}).get("quality", "")
        if tonal_quality:
            tags.append(f"{tonal_quality}声调")

        return tags

    def to_json(self, profile: dict, *, indent: int = 2) -> str:
        """将 Profile 转换为 JSON 字符串。"""
        return json.dumps(profile, ensure_ascii=False, indent=indent)


# 便捷函数
def build_profile(
    artist: str,
    song: str,
    analysis_result: dict,
) -> dict:
    """生成歌手风格档案。"""
    builder = ProfileBuilder()
    return builder.build(artist, song, analysis_result)
