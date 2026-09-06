#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RapFlow 鍒涗綔鍔╂墜 - Web搴旂敤"""

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

st.set_page_config(page_title="RapFlow 鍒涗綔鍔╂墜", page_icon="馃帳", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1DB954; text-align: center; margin-bottom: 1rem; }
    .sub-header { font-size: 1.2rem; color: #666; text-align: center; margin-bottom: 2rem; }
    .result-box { background: #121212; border-radius: 8px; padding: 1rem; margin: 1rem 0; border-left: 4px solid #1DB954; }
    .lyrics-box { background: #1a1a1a; border-radius: 8px; padding: 1rem; margin: 1rem 0; white-space: pre-wrap; font-family: monospace; font-size: 0.9rem; line-height: 1.6; max-height: 500px; overflow-y: auto; }
    .stat-card { background: #121212; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; border-left: 4px solid #1DB954; }
</style>
""", unsafe_allow_html=True)

# 渚ц竟鏍?
with st.sidebar:
    st.markdown("<h2 style='color: #1DB954;'>馃帳 RapFlow</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 馃摎 鍙傝€冮鏍?)
    reference_artist = st.selectbox(
        "妯′豢鍝綅姝屾墜鐨勯鏍硷紵",
        ["Jony J", "椹€濆敮", "娉曡€?, "鍒樿仾", "MC Hotdog", "Tizzy T", "鑷畾涔?],
        key="ref_artist_select",
    )
    if reference_artist == "鑷畾涔?:
        custom_artist = st.text_input(
            "杈撳叆姝屾墜鍚?,
            placeholder="渚嬪锛欸AI",
            key="custom_artist_input",
        )
        if custom_artist:
            reference_artist = custom_artist
    st.markdown("---")
    st.markdown("### 鉁嶏笍 鍒涗綔瑕佹眰")
    topic = st.text_area(
        "涓婚/鍐呭",
        placeholder="渚嬪锛氬寳婕傜殑鏁呬簨銆佸鏂椼€佺埍鎯?..",
        height=100,
        key="topic_textarea",
    )
    mood = st.selectbox(
        "鎯呯华",
        ["婵€鏄?, "娌夌ǔ", "鎮蹭激", "鎰ゆ€?, "杞绘澗", "鎬€鏃?],
        key="mood_select",
    )
    rhyme_density = st.slider(
        "鎶奸煹瀵嗗害",
        1, 10, 7,
        key="rhyme_density_slider",
    )
    flow_style = st.selectbox(
        "Flow椋庢牸",
        ["涓€熷钩琛?, "蹇槾瀵嗛泦", "鎱㈤€熺暀鐧?, "鍒囧垎澶嶆潅"],
        key="flow_style_select",
    )
    model_choice = st.selectbox(
        "LLM 妯″瀷",
        ["agnes-flash (鎺ㄨ崘)", "mock (绂荤嚎棰勮)"],
        key="model_choice",
    )
    llm_model = "agnes-flash" if model_choice.startswith("agnes") else "mock"
    st.markdown("---")
    st.caption("RapFlow v1.0 | 涓枃璇村敱姝岃瘝鍒涗綔鍔╂墜")

# 涓荤晫闈?
st.markdown("<div class='main-header'>馃帳 RapFlow 姝岃瘝鍒涗綔鍔╂墜</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>鍩轰簬 AI 鐨勪腑鏂囪鍞辨瓕璇嶇敓鎴愪笌鍒嗘瀽骞冲彴</div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["馃幍 姝岃瘝鍒涗綔", "馃搳 瀹炴椂鎼滅储", "馃 椋庢牸鍒嗘瀽"])

# 鈹€鈹€ Tab 1锛氭瓕璇嶅垱浣?鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
with tab1:
    # 椤堕儴鎺у埗鏍忥細鍏ㄥ妯帓锛堢敤 container + HTML 鏍峰紡锛屾寜閽湪瀹瑰櫒澶栵級
    st.markdown("<div style='background:#1a1a1a;border-radius:10px;padding:1rem 1.2rem;margin-bottom:0.5rem;'>", unsafe_allow_html=True)
    st.markdown("### 鉁嶏笍 姝岃瘝鍒涗綔")
    col_ctrl1, col_ctrl2 = st.columns([4, 2])
    with col_ctrl1:
        st.markdown(f"**褰撳墠璁剧疆** &nbsp;路&nbsp; 馃帳 {reference_artist} &nbsp;|&nbsp; 馃摑 {topic or '鏈缃富棰?} &nbsp;|&nbsp; 馃幁 {mood}")
    with col_ctrl2:
        st.markdown(f"**鎶奸煹瀵嗗害** `{rhyme_density}/10` &nbsp;路&nbsp; **Flow** {flow_style}")
    st.markdown("</div>", unsafe_allow_html=True)

    # 鎸夐挳鏀惧湪瀹瑰櫒澶栵紝纭繚鐐瑰嚮浜嬩欢姝ｅ父瑙﹀彂
    if not topic:
        st.warning("鈿狅笍 璇峰厛鍦ㄤ晶杈规爮杈撳叆涓婚/鍐呭")
    else:
        created = st.session_state.get("_lyrics_created", False)
        if st.button("馃殌 寮€濮嬪垱浣?, type="primary", key="btn_create"):
            st.session_state["_btn_create_clicked"] = True
            st.session_state["_lyrics_created"] = True
            with st.spinner(f"姝ｅ湪鐢熸垚 {reference_artist} 椋庢牸鐨勬瓕璇?.."):
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
                    ) or "锛堟殏鏃犲弬鑰冩瓕璇嶏級"

                    rhymepct = rhyme_density / 10.0
                    prompts = {
                        "涓€熷钩琛?: "浣跨敤涓瓑璇€燂紝鑺傚骞崇ǔ锛屾娂闊佃嚜鐒舵祦鐣呫€?,
                        "蹇槾瀵嗛泦": "浣跨敤楂橀€熷瘑闆唂low锛屼竴鍒嗛挓鍐呭娆℃崲闊碉紝鎶奸煹瀵嗗害瑕侀珮銆?,
                        "鎱㈤€熺暀鐧?: "浣跨敤鎱㈤€焒low锛屾瘡鍙ヤ箣闂存湁鏄庢樉鍋滈】鐣欑櫧锛岄噸鎯呮劅琛ㄨ揪銆?,
                        "鍒囧垎澶嶆潅": "浣跨敤澶嶆潅鍒囧垎鑺傚锛岄噸闊冲亸绉昏妭鎷嶏紝鍒堕€犳剰澶栫殑寰嬪姩鎰熴€?,
                    }
                    flow_instruction = prompts.get(flow_style, prompts["涓€熷钩琛?])

                    user_prompt = (
                        f"璇蜂负浠ヤ笅鍙傛暟鍒涗綔涓€娈典腑鏂囪鍞辨瓕璇嶏細\n\n"
                        f"鍙傝€冮鏍兼瓕鎵嬶細{reference_artist}\n"
                        f"涓婚/鍐呭锛歿topic}\n"
                        f"鎯呯华锛歿mood}\n"
                        f"鎶奸煹瀵嗗害瑕佹眰锛歿rhymepct:.0%}锛堣秺楂樿秺瀵嗛泦锛塡n"
                        f"Flow瑕佹眰锛歿flow_instruction}\n\n"
                        f"鍙傝€冩瓕鎵嬪師璇嶆牱鏈紙瀛︿範鍏堕鏍硷紝涓嶆槸鎶勮锛夛細\n"
                        f"{ref_lyrics}\n\n"
                        f"璇风洿鎺ヨ緭鍑烘瓕璇嶏紝鏍煎紡瑕佹眰锛歕n"
                        f"1. 鍖呭惈 [Verse 1]銆乕Chorus]銆乕Verse 2]銆乕Chorus] 鍒嗘鏍囪\n"
                        f"2. 姣忔鑷冲皯4琛孿n"
                        f"3. 鎶奸煹鑷劧涓嶇敓纭紝澶氭娂鍔犲垎\n"
                        f"4. 姝岃瘝绉瀬鍚戜笂銆佹湁鎬佸害銆佹湁鐢婚潰鎰焅n"
                        f"5. 鍙緭鍑烘瓕璇嶏紝涓嶈浠讳綍瑙ｉ噴鎴栧紑鍦虹櫧"
                    )
                    system_prompt = (
                        "浣犳槸涓€浣嶄笓涓氱殑涓枃璇村敱姝岃瘝鍒涗綔鑰咃紝鎿呴暱妯′豢涓嶅悓姝屾墜鐨勯鏍笺€?
                        "浣犵簿閫氫腑鏂囨娂闊垫妧宸э紝鍖呮嫭鍗曟娂銆佸弻鎶笺€佷笁鎶笺€佸鎶煎拰鎹㈤煹銆?
                        "浣犵殑姝岃瘝鏃㈡湁鎶€鏈惈閲忓張鏈夋儏鎰熸繁搴︺€?
                    )

                    import httpx
                    api_key = _os.getenv("AGNES_API_KEY", "")
                    if not api_key:
                        raise ValueError("鏈缃?AGNES_API_KEY")

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
                    st.success(f"鉁?{reference_artist} 椋庢牸姝岃瘝宸茬敓鎴愶紒")

                    # 鈹€鈹€ 鍏ㄥ姝岃瘝灞曠ず鍖?鈹€鈹€
                    st.markdown("---")
                    lyr_col1, lyr_col2 = st.columns([4, 1])
                    with lyr_col1:
                        st.markdown("#### 馃摐 鐢熸垚姝岃瘝")
                    with lyr_col2:
                        st.markdown("<div style='text-align:right;font-size:0.85rem;color:#888;'>馃帳 " + reference_artist + " 椋庢牸</div>", unsafe_allow_html=True)
                    st.markdown(f'<div class="lyrics-box" style="min-height:200px;">{generated}</div>', unsafe_allow_html=True)

                    # 鈹€鈹€ 涓夎矾鍒嗘瀽 鈹€鈹€
                    gen_lines = [ln.strip() for ln in generated.split("\n") if ln.strip()]
                    with st.spinner("姝ｅ湪鍒嗘瀽..."):
                        rhyme_analyzer = RhymeAnalyzer()
                        rhyme_results, avg_density, summary, multi_stats = rhyme_analyzer.analyse_lyric(gen_lines)
                        multi_count = 0
                        if multi_stats:
                            multi_count = multi_stats.double_rhyme_lines + multi_stats.triple_rhyme_lines + multi_stats.quad_rhyme_lines

                        st.markdown("---")
                        st.markdown("#### 馃 涓夎矾鍒嗘瀽缁撴灉")
                        mcol1, mcol2, mcol3 = st.columns(3)
                        with mcol1:
                            st.markdown("**馃幍 鎶奸煹鍒嗘瀽**")
                            st.metric("鎶奸煹瀵嗗害", f"{avg_density:.1%}")
                            st.metric("澶氭娂琛屾暟", multi_count)
                        with mcol2:
                            st.markdown("**馃帳 Flow 鍒嗘瀽**")
                            rhyme_densities = [r.rhyme.density if r.rhyme else 0.0 for r in rhyme_results]
                            flow_result = analyze_flow(gen_lines, rhyme_densities)
                            st.metric("Flow 椋庢牸", flow_result.get("style", "?"))
                        with mcol3:
                            st.markdown("**馃幑 澹拌皟鍒嗘瀽**")
                            tonal_result = analyse_lyric_tones(gen_lines)
                            st.metric("澹拌皟娴佺晠搴?, f"{tonal_result['stats']['overall_fluidity_score']:.0f}")
                        st.caption(f"**鎶奸煹鎬荤粨:** {summary}")

                        # 鈹€鈹€ AI 涔愯瘎 鈹€鈹€
                        if llm_model != "mock":
                            with st.spinner("LLM 瑙ｈ涓?.."):
                                llm = LLMAnalyzer(model=llm_model)
                                insight = llm.analyze(
                                    generated,
                                    {"rhyme": {"rhyme_density": avg_density, "summary": summary},
                                     "flow": flow_result,
                                     "tonal": tonal_result},
                                    artist=reference_artist, song="鍘熷垱姝岃瘝",
                                )
                            st.session_state["_insight"] = insight
                            st.markdown("---")
                            st.markdown("#### 馃挰 AI 涔愯瘎")
                            st.markdown(insight)

                    st.session_state["_analysis_done"] = True

                except Exception as exc:
                    st.error(f"鍒涗綔澶辫触: {exc}")
                    logger = logging.getLogger("rapflow_app")
                    logger.warning("鍒涗綔寮傚父: %r", exc)
            st.session_state["_btn_create_clicked"] = False

        # 宸茬敓鎴愭椂閲嶆柊娓叉煋缁撴灉锛堜繚鎸佸竷灞€绋冲畾锛?
        if created and st.session_state.get("_generated_lyrics"):
            generated = st.session_state["_generated_lyrics"]
            ref_artist = st.session_state.get("_generated_artist", reference_artist)

            st.markdown("---")
            lyr_col1, lyr_col2 = st.columns([4, 1])
            with lyr_col1:
                st.markdown("#### 馃摐 鐢熸垚姝岃瘝")
            with lyr_col2:
                st.markdown("<div style='text-align:right;font-size:0.85rem;color:#888;'>馃帳 " + ref_artist + " 椋庢牸</div>", unsafe_allow_html=True)
            st.markdown(f'<div class="lyrics-box" style="min-height:200px;">{generated}</div>', unsafe_allow_html=True)

            if st.session_state.get("_analysis_done"):
                st.markdown("---")
                st.markdown("#### 馃 涓夎矾鍒嗘瀽缁撴灉")
                gen_lines = [ln.strip() for ln in generated.split("\n") if ln.strip()]
                rhyme_analyzer = RhymeAnalyzer()
                rhyme_results, avg_density, summary, multi_stats = rhyme_analyzer.analyse_lyric(gen_lines)
                multi_count = 0
                if multi_stats:
                    multi_count = multi_stats.double_rhyme_lines + multi_stats.triple_rhyme_lines + multi_stats.quad_rhyme_lines
                mcol1, mcol2, mcol3 = st.columns(3)
                with mcol1:
                    st.markdown("**馃幍 鎶奸煹鍒嗘瀽**")
                    st.metric("鎶奸煹瀵嗗害", f"{avg_density:.1%}")
                    st.metric("澶氭娂琛屾暟", multi_count)
                with mcol2:
                    st.markdown("**馃帳 Flow 鍒嗘瀽**")
                    rhyme_densities = [r.rhyme.density if r.rhyme else 0.0 for r in rhyme_results]
                    flow_result = analyze_flow(gen_lines, rhyme_densities)
                    st.metric("Flow 椋庢牸", flow_result.get("style", "?"))
                with mcol3:
                    st.markdown("**馃幑 澹拌皟鍒嗘瀽**")
                    tonal_result = analyse_lyric_tones(gen_lines)
                    st.metric("澹拌皟娴佺晠搴?, f"{tonal_result['stats']['overall_fluidity_score']:.0f}")
                st.caption(f"**鎶奸煹鎬荤粨:** {summary}")

                if llm_model != "mock" and st.session_state.get("_insight"):
                    st.markdown("---")
                    st.markdown("#### 馃挰 AI 涔愯瘎")
                    st.markdown(st.session_state["_insight"])

    st.markdown("---")

# 鈹€鈹€ Tab 2锛氬疄鏃舵悳绱?鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
with tab2:
    st.markdown("### 馃攳 瀹炴椂鎼滅储姝岃瘝")
    col1, col2 = st.columns(2)
    with col1:
        search_artist = st.text_input(
            "姝屾墜鍚?,
            placeholder="渚嬪锛氶┈鎬濆敮",
            key="search_artist_input",
        )
    with col2:
        search_song = st.text_input(
            "姝屽悕",
            placeholder="渚嬪锛歁ade in China",
            key="search_song_input",
        )
    if st.button("Search", type="primary", key="btn_search"):
        if not search_artist or not search_song:
            st.warning("璇疯緭鍏ユ瓕鎵嬪悕鍜屾瓕鍚?)
        else:
            result = None
            show_warning = ""
            with st.spinner(f"Searching '{search_artist} - {search_song}'..."):
                try:
                    result = MusicDlSource().search_lyrics(search_artist, search_song)
                except Exception as e:
                    show_warning = f'鎼滅储澶辫触: {e}'

            if result:
                source_label = {"netease": "缃戞槗浜戦煶涔?, "kugou": "閰风嫍闊充箰"}.get(result['source'], "鑱旂綉")
                st.success(f"鉁?鎵惧埌姝岃瘝锛佹潵婧? {source_label} | 缃俊搴? {result['confidence']:.0%}")
                st.markdown(f"**姝屾墜:** {result['artist']}")
                st.markdown(f"**姝屽悕:** {result['song']}")
            else:
                st.error(f"鏈壘鍒?'{search_artist} - {search_song}' 鐨勬瓕璇?)
                st.info("鎻愮ず锛氳妫€鏌ユ瓕鎵?姝屽悕鎷煎啓锛屾垨灏濊瘯鍏朵粬鍐欐硶")

            if show_warning:
                st.warning(show_warning)

            # 鏈夌粨鏋滃垯灞曠ず姝岃瘝鍜屽垎鏋?
            if result:
                st.markdown("---")
                raw_lyrics = result.get('lyrics', '')
                clean_lyrics = re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', raw_lyrics)
                clean_lyrics = re.sub(r'\[(Chorus|Verse|Intro|Outro|Bridge|Hook)\]', '', clean_lyrics)
                clean_lyrics = '\n'.join(line.strip() for line in clean_lyrics.split('\n') if line.strip())

                st.markdown("#### 馃摐 姝岃瘝鍐呭")
                st.markdown(f'<div class="lyrics-box">{clean_lyrics}</div>', unsafe_allow_html=True)

                # 涓夎矾鍒嗘瀽
                st.markdown("---")
                st.markdown("#### 馃 姝岃瘝鍒嗘瀽")

                lines = [line.strip() for line in clean_lyrics.split('\n') if line.strip()]

                with st.spinner("姝ｅ湪鍒嗘瀽..."):
                    try:
                        rhyme_analyzer = RhymeAnalyzer()
                        rhyme_results, avg_density, summary, multi_stats = rhyme_analyzer.analyse_lyric(lines)

                        multi_count = 0
                        if multi_stats:
                            multi_count = multi_stats.double_rhyme_lines + multi_stats.triple_rhyme_lines + multi_stats.quad_rhyme_lines

                        col_a1, col_a2, col_a3 = st.columns(3)
                        with col_a1:
                            st.markdown("#### 馃幍 鎶奸煹鍒嗘瀽")
                            st.metric("鎶奸煹瀵嗗害", f"{avg_density:.1%}")
                            st.metric("澶氭娂琛屾暟", multi_count)
                        with col_a2:
                            st.markdown("#### 馃帳 Flow 鍒嗘瀽")
                            rhyme_densities = [r.rhyme.density if r.rhyme else 0.0 for r in rhyme_results]
                            flow_result = analyze_flow(lines, rhyme_densities)
                            st.metric("Flow 椋庢牸", flow_result['style'])
                        with col_a3:
                            st.markdown("#### 馃幑 澹拌皟鍒嗘瀽")
                            tonal_result = analyse_lyric_tones(lines)
                            st.metric("澹拌皟娴佺晠搴?, f"{tonal_result['stats']['overall_fluidity_score']:.0f}")

                        st.markdown(f"**鎶奸煹鎬荤粨:** {summary}")
                        if 'details' in flow_result:
                            st.caption(flow_result['details'])
                        if tonal_result.get('feedback'):
                            st.markdown("**澹拌皟寤鸿:**")
                            for fb in tonal_result['feedback'][:3]:
                                st.caption(f"鈥?{fb}")
                    except Exception as e:
                        st.warning(f"鍒嗘瀽澶辫触: {e}")
                        import traceback
                        st.code(traceback.format_exc())

# 鈹€鈹€ Tab 3锛氶鏍煎垎鏋?鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
with tab3:
    st.markdown("### 馃 姝屾墜椋庢牸鍒嗘瀽")
    col1, col2 = st.columns(2)
    with col1:
        analyze_artist = st.text_input(
            "姝屾墜鍚?,
            placeholder="渚嬪锛氶┈鎬濆敮",
            key="analyze_artist_input",
        )
    with col2:
        analyze_song = st.text_input(
            "姝屽悕锛堝彲閫夛級",
            placeholder="渚嬪锛歁ade in China",
            key="analyze_song_input",
        )
    if st.button("鍒嗘瀽椋庢牸", type="primary", key="btn_analyze"):
        if not analyze_artist:
            st.warning("璇疯緭鍏ユ瓕鎵嬪悕")
        else:
            with st.spinner(f"姝ｅ湪鍒嗘瀽 {analyze_artist} 鐨勯鏍?.."):
                try:
                    import sqlite3
                    db_path = Path(__file__).parent / "lyrics-crawler" / "data" / "lyrics_corpus.db"
                    conn = sqlite3.connect(str(db_path))
                    c = conn.cursor()
                    c.execute("SELECT song, raw_lyrics FROM lyrics WHERE artist LIKE ? LIMIT 3", (f"%{analyze_artist}%",))
                    songs = c.fetchall()
                    conn.close()
                    if not songs:
                        st.error(f"鏈壘鍒?'{analyze_artist}' 鐨勬瓕鏇?)
                    else:
                        song_name, lyrics = songs[0]
                        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
                        rhyme_analyzer = RhymeAnalyzer()
                        rhyme_results, avg_density, summary, multi_stats = rhyme_analyzer.analyse_lyric(lines)
                        rhyme_densities = [r.rhyme.density if r.rhyme else 0.0 for r in rhyme_results]

                        flow_result = analyze_flow(lines, rhyme_densities)
                        tonal_result = analyse_lyric_tones(lines)

                        st.success(f"鍒嗘瀽瀹屾垚锛佹壘鍒?{len(songs)} 棣栨瓕")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown("#### 馃幍 鎶奸煹鍒嗘瀽")
                            st.metric("鎶奸煹瀵嗗害", f"{avg_density:.0%}")
                            multi_count = 0
                            if multi_stats:
                                multi_count = multi_stats.double_rhyme_lines + multi_stats.triple_rhyme_lines + multi_stats.quad_rhyme_lines
                            st.metric("澶氭娂琛屾暟", multi_count)
                        with col2:
                            st.markdown("#### 馃帳 Flow 鍒嗘瀽")
                            st.metric("Flow 椋庢牸", flow_result['style'])
                        with col3:
                            st.markdown("#### 馃幑 澹拌皟鍒嗘瀽")
                            st.metric("澹拌皟娴佺晠搴?, f"{tonal_result['stats']['overall_fluidity_score']:.0f}")
                        st.markdown("---")
                        st.markdown(f"**鎶奸煹鎬荤粨:** {summary}")
                        if 'details' in flow_result:
                            st.caption(flow_result['details'])
                        if tonal_result.get('feedback'):
                            st.markdown("**澹拌皟寤鸿:**")
                            for fb in tonal_result['feedback'][:3]:
                                st.caption(f"鈥?{fb}")
                except Exception as e:
                    st.error(f"鍒嗘瀽澶辫触: {e}")
                    import traceback
                    st.code(traceback.format_exc())

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666; padding: 1rem;'><p>RapFlow v1.0 | 涓枃璇村敱姝岃瘝鍒涗綔鍔╂墜</p><p>缃戞槗浜?+ 閰风嫍 | 3-Way Analysis</p></div>", unsafe_allow_html=True)
