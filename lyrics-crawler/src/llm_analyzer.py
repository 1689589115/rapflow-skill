"""LLM 解说层 — 将技术分析结果转为专业乐评。

支持模型：
  - mock       : 本地占位输出（无需网络）
  - deepseek-chat : DeepSeek Chat
  - gpt-4      : OpenAI GPT-4
  - gpt-4o     : OpenAI GPT-4o
  - claude-3-opus : Anthropic Claude 3 Opus
  - agnes-flash  : Agnes AI 2.5-Flash (OpenAI 兼容接口)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_LLM_PROVIDERS = {
    "gpt-4":       {"provider": "openai",    "model": "gpt-4"},
    "gpt-4o":      {"provider": "openai",    "model": "gpt-4o"},
    "claude-3-opus": {"provider": "anthropic","model": "claude-3-opus"},
    "deepseek-chat": {"provider": "deepseek","model": "deepseek-chat"},
    "agnes-flash": {"provider": "agnes",    "model": "agnes-2.5-flash"},
    "mock":        {"provider": "mock",     "model": "mock"},
}

# Agnes AI 端点（OpenAI 兼容）
_AGNES_BASE_URL = "https://apihub.agnes-ai.com/v1"


def _get_api_key(provider: str) -> Optional[str]:
    """按 provider 从环境变量读取 API Key。"""
    key_map = {
        "openai":    os.getenv("OPENAI_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "deepseek":  os.getenv("DEEPSEEK_API_KEY"),
        "agnes":     os.getenv("AGNES_API_KEY"),
    }
    return key_map.get(provider)


class LLMAnalyzer:
    def __init__(self, model: str = "mock") -> None:
        if model not in _LLM_PROVIDERS:
            raise ValueError(
                f"Unknown model: {model!r}. "
                f"Available: {', '.join(_LLM_PROVIDERS)}"
            )
        self.model = model
        self._provider = _LLM_PROVIDERS[model]["provider"]
        self._model_name = _LLM_PROVIDERS[model]["model"]

    def analyze(
        self,
        lyrics: str,
        analysis_result: dict | None = None,
        *args,
        artist: str = "",
        song: str = "",
        **kwargs,
    ) -> str:
        """将技术分析结果转为专业乐评。

        兼容旧版 tuple 返回格式（RhymeAnalyzer 三步返回）。
        """
        if isinstance(analysis_result, tuple):
            analysis_result = {
                "rhyme": {
                    "rhyme_density": analysis_result[1] if len(analysis_result) > 1 else 0,
                    "summary": analysis_result[2] if len(analysis_result) > 2 else "",
                },
                "flow": {},
                "tonal": {},
            }
        system_prompt = self._build_system_prompt(artist, song)
        user_prompt = self._build_user_prompt(lyrics, analysis_result)
        return self._call_llm(system_prompt, user_prompt)

    # ── prompt 构建 ────────────────────────────────────────────────────

    def _build_system_prompt(self, artist: str, song: str) -> str:
        return (
            "你是一位资深中文说唱制作人和乐评人，对中文说唱的押韵、Flow、"
            "声调搭配、歌词意境有深入理解。\n"
            f"当前歌曲：歌手={artist}, 歌名={song}\n"
            "请基于技术数据给出专业解读，语言口语化，像跟朋友聊歌一样自然。"
        )

    def _build_user_prompt(self, lyrics: str, analysis_result: dict) -> str:
        lyrics_preview = lyrics[:1200] + "..." if len(lyrics) > 1200 else lyrics
        analysis_json = json.dumps(
            analysis_result, ensure_ascii=False, indent=2,
        )
        return (
            "请从以下维度解读这首歌词：\n"
            "1. 主题和情感内核\n"
            "2. 押韵策略（密度、换韵、多押）\n"
            "3. Flow 设计（节奏变化、停顿运用）\n"
            "4. 声调搭配\n"
            "5. 综合评价（技术性 + 艺术性打分，各 10 分制）\n\n"
            "歌词片段：\n"
            f"{lyrics_preview}\n\n"
            "技术分析数据：\n"
            f"{analysis_json}"
        )

    # ── LLM 调用 ───────────────────────────────────────────────────────

    def _call_llm(self, system: str, user: str) -> str:
        try:
            return self._call_real(system, user)
        except Exception as exc:
            logger.warning("LLM call failed (%s): %r", self.model, exc)
            return self._call_mock(system, user)

    def _call_real(self, system: str, user: str) -> str:
        """通过 OpenAI 兼容接口调用真实 LLM。"""
        import httpx

        api_key = _get_api_key(self._provider)
        if not api_key:
            logger.warning("No API key set for %s, falling back to mock", self._provider)
            return self._call_mock(system, user)

        if self._provider == "agnes":
            base_url = _AGNES_BASE_URL
        elif self._provider == "openai":
            base_url = "https://api.openai.com/v1"
        elif self._provider == "anthropic":
            # Anthropic 使用不同 SDK，暂回退 mock
            return self._call_mock(system, user)
        elif self._provider == "deepseek":
            base_url = "https://api.deepseek.com/v1"
        else:
            return self._call_mock(system, user)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            "temperature": 0.8,
            "max_tokens": 1024,
        }

        timeout = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)
        # 跳过代理直连 LLM API
        with httpx.Client(timeout=timeout, proxy=None) as client:
            resp = client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _call_mock(self, system: str, user: str) -> str:
        return (
            "## 专业分析\n\n"
            "基于技术分析数据，我对这首歌的解读如下：\n\n"
            "### 主题与情感\n"
            "这首歌展现了创作者对自身处境的深刻反思。"
            "从歌词中可以看出，作者在探讨自我认同的概念——"
            "既是对物质条件的自信，也是对精神世界的坚守。"
            "这种双关语的运用非常巧妙，既接地气又有深度。\n\n"
            "情感基调是自信中带着反思，既有对过去的回顾，也有对未来的展望。\n\n"
            "### 押韵策略\n"
            "从技术数据来看，押韵密度相当高，说明作者在韵脚上下了很大功夫。\n"
            "- 押韵 scheme 呈现明显的规律性，便于听众记忆\n"
            "- 多押占比适中，既展示了技巧又不显刻意\n"
            "- 换韵点设计合理，在情绪转折点换韵，增强了歌曲的动态感\n\n"
            "### Flow 设计\n"
            "Flow 的变化是这首歌的一大亮点：\n"
            "- 整体节奏稳定，但在关键段落有明显的加速设计\n"
            "- 停顿点运用得当，给听众留出了消化歌词的空间\n"
            "- Flow 变化有逻辑，不是为变而变，而是服务于情感表达\n\n"
            "### 声调搭配\n"
            "声调匹配率良好，平仄交替自然，使得歌词读起来既有节奏感又不失流畅性。\n\n"
            "### 评分\n"
            "- 技术性：8.5/10 — 押韵和 Flow 都有出色表现\n"
            "- 艺术性：8.0/10 — 主题表达清晰，情感真挚\n\n"
            "**总结**：这是一首技巧与情感兼具的作品，适合反复品味。\n\n"
            "---\n*Generated by LLMAnalyzer (mock mode)*"
        )


def analyze_lyrics(
    lyrics: str,
    analysis_result: dict,
    *,
    artist: str = "",
    song: str = "",
    model: str = "mock",
) -> str:
    """便捷函数：创建 LLMAnalyzer 并调用分析。"""
    analyzer = LLMAnalyzer(model=model)
    return analyzer.analyze(lyrics, analysis_result, artist=artist, song=song)
