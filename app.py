#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RapFlow 创作助手 - Web应用"""

import streamlit as st
import sys
import re
import logging
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent / "lyrics-crawler"))
sys.path.insert(0, str(Path(__file__).parent / "clean-rapflow-skill"))

from crawler.sources.music_dl_source import MusicDlSource
from skill import RhymeAnalyzer, analyze_flow, analyse_lyric_tones
from src.llm_analyzer import LLMAnalyzer

import dotenv
dotenv.load_dotenv()

# Cloud 环境优先从 streamlit secrets 读取，兜底本地环境变量
_secret_key = ""
try:
    _secret_key = st.secrets["agnes"]["api_key"]
except Exception:
    pass
import os as _os
# secrets 非空时始终覆盖（优先级高于 .env）
if _secret_key:
    _os.environ["AGNES_API_KEY"] = _secret_key

print('=' * 50)
print('RapFlow v1.0 startup...')
print('http://localhost:8501')
print('=' * 50)

def _check_deps():
    missing = []
    for mod, name in [('streamlit','streamlit'),('httpx','httpx'),('pypinyin','pypinyin'),('requests','requests')]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(name)
    return missing

_missing = _check_deps()
if _missing:
    import sys as _sys
    print(f'ERROR: missing deps: {_missing}', file=_sys.stderr)
    _sys.exit(1)

st.set_page_config(page_title="RapFlow 创作助手", page_icon="🎤", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1DB954; text-align: center; margin-bottom: 1rem; }
    .sub-header { font-size: 1.2rem; color: #666; text-align: center; margin-bottom: 2rem; }
    .result-box { background: #121212; border-radius: 8px; padding: 1rem; margin: 1rem 0; border-left: 4px solid #1DB954; }
    .lyrics-box { background: #1a1a1a; border-radius: 8px; padding: 1rem; margin: 1rem 0; white-space: pre-wrap; font-family: monospace; font-size: 0.9rem; line-height: 1.6; max-height: 500px; overflow-y: auto; }
    .stat-card { background: #121212; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; border-left: 4px solid #1DB954; }
</style>
""", unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.markdown("<h2 style='color: #1DB954;'>🎤 RapFlow</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📚 参考风格")
    reference_artist = st.selectbox(
        "模仿哪位歌手的风格？",
        ["Jony J", "马思唯", "法老", "刘聪", "MC Hotdog", "Tizzy T", "自定义"],
        key="ref_artist_select",
    )
    if reference_artist == "自定义":
        custom_artist = st.text_input(
            "输入歌手名",
            placeholder="例如：GAI",
            key="custom_artist_input",
        )
        if custom_artist:
            reference_artist = custom_artist
    st.markdown("---")
    st.markdown("### ✍️ 创作要求")
    topic = st.text_area(
        "主题/内容",
        placeholder="例如：北漂的故事、奋斗、爱情...",
        height=100,
        key="topic_textarea",
    )
    mood = st.selectbox(
        "情绪",
        ["激昂", "沉稳", "悲伤", "愤怒", "轻松", "怀旧"],
        key="mood_select",
    )
    rhyme_density = st.slider(
        "押韵密度",
        1, 10, 7,
        key="rhyme_density_slider",
    )
    flow_style = st.selectbox(
        "Flow风格",
        ["中速平衡", "快嘴密集", "慢速留白", "切分复杂"],
        key="flow_style_select",
    )
    model_choice = st.selectbox(
        "LLM 模型",
        ["agnes-flash (推荐)", "mock (离线预览)"],
        key="model_choice",
    )
    llm_model = "agnes-flash" if model_choice.startswith("agnes") else "mock"
    st.markdown("---")
    st.caption("RapFlow v1.0 | 中文说唱歌词创作助手")

# 主界面
st.markdown("<div class='main-header'>🎤 RapFlow 歌词创作助手</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>基于 AI 的中文说唱歌词生成与分析平台</div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🎵 歌词创作", "📊 实时搜索", "🧠 风格分析"])

# ── Tab 1：歌词创作 ───────────────────────────────────────────────────────
with tab1:
    # 顶部控制栏：全宽横排（用 container + HTML 样式，按钮在容器外）
    st.markdown("<div style='background:#1a1a1a;border-radius:10px;padding:1rem 1.2rem;margin-bottom:0.5rem;'>", unsafe_allow_html=True)
    st.markdown("### ✍️ 歌词创作")
    col_ctrl1, col_ctrl2 = st.columns([4, 2])
    with col_ctrl1:
        st.markdown(f"**当前设置** &nbsp;·&nbsp; 🎤 {reference_artist} &nbsp;|&nbsp; 📝 {topic or '未设置主题'} &nbsp;|&nbsp; 🎭 {mood}")
    with col_ctrl2:
        st.markdown(f"**押韵密度** `{rhyme_density}/10` &nbsp;·&nbsp; **Flow** {flow_style}")
    st.markdown("</div>", unsafe_allow_html=True)

    # 按钮放在容器外，确保点击事件正常触发
    if not topic:
        st.warning("⚠️ 请先在侧边栏输入主题/内容")
    else:
        created = st.session_state.get("_lyrics_created", False)
        if st.button("🚀 开始创作", type="primary", key="btn_create"):
            st.session_state["_btn_create_clicked"] = True
            st.session_state["_lyrics_created"] = True
            with st.spinner(f"正在生成 {reference_artist} 风格的歌词..."):
                try:
                    import sqlite3
                    db_path = Path(__file__).parent / "lyrics-crawler" / "data" / "lyrics_corpus.db"
                    conn = sqlite3.connect(str(db_path))
                    c = conn.cursor()
                    c.execute(
                        "SELECT song, clean_lyrics FROM lyrics WHERE artist LIKE ? ORDER BY RANDOM() LIMIT 3",
                        (f"%{reference_artist}%",),
                    )
                    ref_songs = c.fetchall()
                    conn.close()
                    ref_lyrics = "\n\n---\n\n".join(
                        f"[{s[0]}]\n{s[1]}" for s in ref_songs if s[1]
                    ) or "（暂无参考歌词）"

                    rhymepct = rhyme_density / 10.0
                    prompts = {
                        "中速平衡": "使用中等语速，节奏平稳，押韵自然流畅。",
                        "快嘴密集": "使用高速密集flow，一分钟内多次换韵，押韵密度要高。",
                        "慢速留白": "使用慢速flow，每句之间有明显停顿留白，重情感表达。",
                        "切分复杂": "使用复杂切分节奏，重音偏移节拍，制造意外的律动感。",
                    }
                    flow_instruction = prompts.get(flow_style, prompts["中速平衡"])

                    user_prompt = (
                        f"请为以下参数创作一段中文说唱歌词：\n\n"
                        f"参考风格歌手：{reference_artist}\n"
                        f"主题/内容：{topic}\n"
                        f"情绪：{mood}\n"
                        f"押韵密度要求：{rhymepct:.0%}（越高越密集）\n"
                        f"Flow要求：{flow_instruction}\n\n"
                        f"参考歌手原词样本（学习其风格，不是抄袭）：\n"
                        f"{ref_lyrics}\n\n"
                        f"请直接输出歌词，格式要求：\n"
                        f"1. 包含 [Verse 1]、[Chorus]、[Verse 2]、[Chorus] 分段标记\n"
                        f"2. 每段至少4行\n"
                        f"3. 押韵自然不生硬，多押加分\n"
                        f"4. 歌词积极向上、有态度、有画面感\n"
                        f"5. 只输出歌词，不要任何解释或开场白"
                    )
                    system_prompt = (
                        "你是一位专业的中文说唱歌词创作者，擅长模仿不同歌手的风格。"
                        "你精通中文押韵技巧，包括单押、双押、三押、多押和换韵。"
                        "你的歌词既有技术含量又有情感深度。"
                    )

                    import httpx
                    api_key = _os.getenv("AGNES_API_KEY", "")
                    if not api_key:
                        raise ValueError("未设置 AGNES_API_KEY")

                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    }
                    payload = {
                        "model": "agnes-2.5-flash",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user",   "content": user_prompt},
                        ],
                        "temperature": 0.9,
                        "max_tokens": 1500,
                    }
                    timeout = httpx.Timeout(connect=10.0, read=90.0, write=30.0, pool=10.0)
                    with httpx.Client(timeout=timeout, proxy=None) as client:
                        resp = client.post(
                            "https://apihub.agnes-ai.com/v1/chat/completions",
                            headers=headers, json=payload,
                        )
                        resp.raise_for_status()
                        generated = resp.json()["choices"][0]["message"]["content"]
                    st.session_state["_generated_lyrics"] = generated
                    st.session_state["_generated_artist"] = reference_artist
                    st.success(f"✅ {reference_artist} 风格歌词已生成！")

                    # ── 全宽歌词展示区 ──
                    st.markdown("---")
                    lyr_col1, lyr_col2 = st.columns([4, 1])
                    with lyr_col1:
                        st.markdown("#### 📜 生成歌词")
                    with lyr_col2:
                        st.markdown("<div style='text-align:right;font-size:0.85rem;color:#888;'>🎤 " + reference_artist + " 风格</div>", unsafe_allow_html=True)
                    st.markdown(f'<div class="lyrics-box" style="min-height:200px;">{generated}</div>', unsafe_allow_html=True)

                    # ── 三路分析 ──
                    gen_lines = [ln.strip() for ln in generated.split("\n") if ln.strip()]
                    with st.spinner("正在分析..."):
                        rhyme_analyzer = RhymeAnalyzer()
                        rhyme_results, avg_density, summary, multi_stats = rhyme_analyzer.analyse_lyric(gen_lines)
                        multi_count = 0
                        if multi_stats:
                            multi_count = multi_stats.double_rhyme_lines + multi_stats.triple_rhyme_lines + multi_stats.quad_rhyme_lines

                        st.markdown("---")
                        st.markdown("#### 🧠 三路分析结果")
                        mcol1, mcol2, mcol3 = st.columns(3)
                        with mcol1:
                            st.markdown("**🎵 押韵分析**")
                            st.metric("押韵密度", f"{avg_density:.1%}")
                            st.metric("多押行数", multi_count)
                        with mcol2:
                            st.markdown("**🎤 Flow 分析**")
                            rhyme_densities = [r.rhyme.density if r.rhyme else 0.0 for r in rhyme_results]
                            flow_result = analyze_flow(gen_lines, rhyme_densities)
                            st.metric("Flow 风格", flow_result.get("style", "?"))
                        with mcol3:
                            st.markdown("**🎹 声调分析**")
                            tonal_result = analyse_lyric_tones(gen_lines)
                            st.metric("声调流畅度", f"{tonal_result['stats']['overall_fluidity_score']:.0f}")
                        st.caption(f"**押韵总结:** {summary}")

                        # ── AI 乐评 ──
                        if llm_model != "mock":
                            with st.spinner("LLM 解说中..."):
                                llm = LLMAnalyzer(model=llm_model)
                                insight = llm.analyze(
                                    generated,
                                    {"rhyme": {"rhyme_density": avg_density, "summary": summary},
                                     "flow": flow_result,
                                     "tonal": tonal_result},
                                    artist=reference_artist, song="原创歌词",
                                )
                            st.session_state["_insight"] = insight
                            st.markdown("---")
                            st.markdown("#### 💬 AI 乐评")
                            st.markdown(insight)

                    st.session_state["_analysis_done"] = True

                except Exception as exc:
                    st.error(f"创作失败: {exc}")
                    logger = logging.getLogger("rapflow_app")
                    logger.warning("创作异常: %r", exc)
            st.session_state["_btn_create_clicked"] = False

        # 已生成时重新渲染结果（保持布局稳定）
        if created and st.session_state.get("_generated_lyrics"):
            generated = st.session_state["_generated_lyrics"]
            ref_artist = st.session_state.get("_generated_artist", reference_artist)

            st.markdown("---")
            lyr_col1, lyr_col2 = st.columns([4, 1])
            with lyr_col1:
                st.markdown("#### 📜 生成歌词")
            with lyr_col2:
                st.markdown("<div style='text-align:right;font-size:0.85rem;color:#888;'>🎤 " + ref_artist + " 风格</div>", unsafe_allow_html=True)
            st.markdown(f'<div class="lyrics-box" style="min-height:200px;">{generated}</div>', unsafe_allow_html=True)

            if st.session_state.get("_analysis_done"):
                st.markdown("---")
                st.markdown("#### 🧠 三路分析结果")
                gen_lines = [ln.strip() for ln in generated.split("\n") if ln.strip()]
                rhyme_analyzer = RhymeAnalyzer()
                rhyme_results, avg_density, summary, multi_stats = rhyme_analyzer.analyse_lyric(gen_lines)
                multi_count = 0
                if multi_stats:
                    multi_count = multi_stats.double_rhyme_lines + multi_stats.triple_rhyme_lines + multi_stats.quad_rhyme_lines
                mcol1, mcol2, mcol3 = st.columns(3)
                with mcol1:
                    st.markdown("**🎵 押韵分析**")
                    st.metric("押韵密度", f"{avg_density:.1%}")
                    st.metric("多押行数", multi_count)
                with mcol2:
                    st.markdown("**🎤 Flow 分析**")
                    rhyme_densities = [r.rhyme.density if r.rhyme else 0.0 for r in rhyme_results]
                    flow_result = analyze_flow(gen_lines, rhyme_densities)
                    st.metric("Flow 风格", flow_result.get("style", "?"))
                with mcol3:
                    st.markdown("**🎹 声调分析**")
                    tonal_result = analyse_lyric_tones(gen_lines)
                    st.metric("声调流畅度", f"{tonal_result['stats']['overall_fluidity_score']:.0f}")
                st.caption(f"**押韵总结:** {summary}")

                if llm_model != "mock" and st.session_state.get("_insight"):
                    st.markdown("---")
                    st.markdown("#### 💬 AI 乐评")
                    st.markdown(st.session_state["_insight"])

    st.markdown("---")

# ── Tab 2：实时搜索 ──────────────────────────────────────────────────────
with tab2:
    st.markdown("### 🔍 实时搜索歌词")
    col1, col2 = st.columns(2)
    with col1:
        search_artist = st.text_input(
            "歌手名",
            placeholder="例如：马思唯",
            key="search_artist_input",
        )
    with col2:
        search_song = st.text_input(
            "歌名",
            placeholder="例如：Made in China",
            key="search_song_input",
        )
    if st.button("Search", type="primary", key="btn_search"):
        if not search_artist or not search_song:
            st.warning("请输入歌手名和歌名")
        else:
            result = None
            show_warning = ""
            with st.spinner(f"Searching '{search_artist} - {search_song}'..."):
                try:
                    result = MusicDlSource().search_lyrics(search_artist, search_song)
                except Exception as e:
                    show_warning = f'搜索失败: {e}'

            if result:
                source_label = {"netease": "网易云音乐", "kugou": "酷狗音乐"}.get(result['source'], "联网")
                st.success(f"✅ 找到歌词！来源: {source_label} | 置信度: {result['confidence']:.0%}")
                st.markdown(f"**歌手:** {result['artist']}")
                st.markdown(f"**歌名:** {result['song']}")
            else:
                st.error(f"未找到 '{search_artist} - {search_song}' 的歌词")
                st.info("提示：请检查歌手/歌名拼写，或尝试其他写法")

            if show_warning:
                st.warning(show_warning)

            # 有结果则展示歌词和分析
            if result:
                st.markdown("---")
                raw_lyrics = result.get('lyrics', '')
                clean_lyrics = re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', raw_lyrics)
                clean_lyrics = re.sub(r'\[(Chorus|Verse|Intro|Outro|Bridge|Hook)\]', '', clean_lyrics)
                clean_lyrics = '\n'.join(line.strip() for line in clean_lyrics.split('\n') if line.strip())

                st.markdown("#### 📜 歌词内容")
                st.markdown(f'<div class="lyrics-box">{clean_lyrics}</div>', unsafe_allow_html=True)

                # 三路分析
                st.markdown("---")
                st.markdown("#### 🧠 歌词分析")

                lines = [line.strip() for line in clean_lyrics.split('\n') if line.strip()]

                with st.spinner("正在分析..."):
                    try:
                        rhyme_analyzer = RhymeAnalyzer()
                        rhyme_results, avg_density, summary, multi_stats = rhyme_analyzer.analyse_lyric(lines)

                        multi_count = 0
                        if multi_stats:
                            multi_count = multi_stats.double_rhyme_lines + multi_stats.triple_rhyme_lines + multi_stats.quad_rhyme_lines

                        col_a1, col_a2, col_a3 = st.columns(3)
                        with col_a1:
                            st.markdown("#### 🎵 押韵分析")
                            st.metric("押韵密度", f"{avg_density:.1%}")
                            st.metric("多押行数", multi_count)
                        with col_a2:
                            st.markdown("#### 🎤 Flow 分析")
                            rhyme_densities = [r.rhyme.density if r.rhyme else 0.0 for r in rhyme_results]
                            flow_result = analyze_flow(lines, rhyme_densities)
                            st.metric("Flow 风格", flow_result['style'])
                        with col_a3:
                            st.markdown("#### 🎹 声调分析")
                            tonal_result = analyse_lyric_tones(lines)
                            st.metric("声调流畅度", f"{tonal_result['stats']['overall_fluidity_score']:.0f}")

                        st.markdown(f"**押韵总结:** {summary}")
                        if 'details' in flow_result:
                            st.caption(flow_result['details'])
                        if tonal_result.get('feedback'):
                            st.markdown("**声调建议:**")
                            for fb in tonal_result['feedback'][:3]:
                                st.caption(f"• {fb}")
                    except Exception as e:
                        st.warning(f"分析失败: {e}")
                        import traceback
                        st.code(traceback.format_exc())

# ── Tab 3：风格分析 ──────────────────────────────────────────────────────
with tab3:
    st.markdown("### 🧠 歌手风格分析")
    col1, col2 = st.columns(2)
    with col1:
        analyze_artist = st.text_input(
            "歌手名",
            placeholder="例如：马思唯",
            key="analyze_artist_input",
        )
    with col2:
        analyze_song = st.text_input(
            "歌名（可选）",
            placeholder="例如：Made in China",
            key="analyze_song_input",
        )
    if st.button("分析风格", type="primary", key="btn_analyze"):
        if not analyze_artist:
            st.warning("请输入歌手名")
        else:
            with st.spinner(f"正在分析 {analyze_artist} 的风格..."):
                try:
                    import sqlite3
                    db_path = Path(__file__).parent / "lyrics-crawler" / "data" / "lyrics_corpus.db"
                    conn = sqlite3.connect(str(db_path))
                    c = conn.cursor()
                    c.execute("SELECT song, raw_lyrics FROM lyrics WHERE artist LIKE ? LIMIT 3", (f"%{analyze_artist}%",))
                    songs = c.fetchall()
                    conn.close()
                    if not songs:
                        st.error(f"未找到 '{analyze_artist}' 的歌曲")
                    else:
                        song_name, lyrics = songs[0]
                        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
                        rhyme_analyzer = RhymeAnalyzer()
                        rhyme_results, avg_density, summary, multi_stats = rhyme_analyzer.analyse_lyric(lines)
                        rhyme_densities = [r.rhyme.density if r.rhyme else 0.0 for r in rhyme_results]

                        flow_result = analyze_flow(lines, rhyme_densities)
                        tonal_result = analyse_lyric_tones(lines)

                        st.success(f"分析完成！找到 {len(songs)} 首歌")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown("#### 🎵 押韵分析")
                            st.metric("押韵密度", f"{avg_density:.0%}")
                            multi_count = 0
                            if multi_stats:
                                multi_count = multi_stats.double_rhyme_lines + multi_stats.triple_rhyme_lines + multi_stats.quad_rhyme_lines
                            st.metric("多押行数", multi_count)
                        with col2:
                            st.markdown("#### 🎤 Flow 分析")
                            st.metric("Flow 风格", flow_result['style'])
                        with col3:
                            st.markdown("#### 🎹 声调分析")
                            st.metric("声调流畅度", f"{tonal_result['stats']['overall_fluidity_score']:.0f}")
                        st.markdown("---")
                        st.markdown(f"**押韵总结:** {summary}")
                        if 'details' in flow_result:
                            st.caption(flow_result['details'])
                        if tonal_result.get('feedback'):
                            st.markdown("**声调建议:**")
                            for fb in tonal_result['feedback'][:3]:
                                st.caption(f"• {fb}")
                except Exception as e:
                    st.error(f"分析失败: {e}")
                    import traceback
                    st.code(traceback.format_exc())

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666; padding: 1rem;'><p>RapFlow v1.0 | 中文说唱歌词创作助手</p><p>网易云 + 酷狗 | 3-Way Analysis</p></div>", unsafe_allow_html=True)
