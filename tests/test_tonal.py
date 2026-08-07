# -*- coding: utf-8 -*-
"""
声调搭配分析模块测试 - v1.5.0
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from skill import RapFlowSkill
from skill.tonal_analyzer import (
    analyse_lyric_tones,
    _extract_tone_sequence,
    _classify_pattern,
    _shannon_entropy,
    _calc_transition_ratios,
    _get_char_tone,
)


def test_flat_tone():
    """全是阴平（一声）的句子 → pattern_type == 'flat'"""
    print("\n[TEST] flat tone pattern")
    line = "天天天天天空空空空"
    tones = _extract_tone_sequence(line)
    pattern = _classify_pattern(tones)
    assert pattern == "flat", f"Expected 'flat', got '{pattern}' (tones={tones})"
    print(f"  [PASS] flat pattern: tones={tones}, pattern={pattern}")


def test_alternating_tone():
    """刻意构造高低交替的句子 → pattern_type == 'alternating'"""
    print("\n[TEST] alternating tone pattern")
    # 1→2→1→2 交替
    line = "天昂天昂天昂天昂"
    tones = _extract_tone_sequence(line)
    pattern = _classify_pattern(tones)
    assert pattern == "alternating", f"Expected 'alternating', got '{pattern}' (tones={tones})"
    print(f"  [PASS] alternating pattern: tones={tones}, pattern={pattern}")


def test_wave_tone():
    """有一定起伏但不够规律的句子 → pattern_type == 'wave'"""
    print("\n[TEST] wave tone pattern")
    line = "小镇男孩现在做着嘻哈"
    tones = _extract_tone_sequence(line)
    pattern = _classify_pattern(tones)
    # 波动的句子应该是 wave
    assert pattern in ("wave", "alternating"), f"Expected 'wave' or 'alternating', got '{pattern}' (tones={tones})"
    print(f"  [PASS] wave pattern: tones={tones}, pattern={pattern}")


def test_mixed_nonchinese():
    """中英文混排句子 → 英文/tone=-1 不干扰计算"""
    print("\n[TEST] mixed Chinese-English tone sequence")
    line = "yo I'm gonna 飞得更高"
    tones = _extract_tone_sequence(line)
    # 非汉字应全部为 -1，汉字应有正确声调
    chinese_tones = [t for t in tones if t != -1]
    assert len(chinese_tones) > 0, "should have some Chinese tones"
    # 检查 '飞'(fei1) '得'(de2) '更'(geng4) '高'(gao1)
    assert 1 in chinese_tones, "should have tone 1 (飞)"
    assert 2 in chinese_tones, "should have tone 2 (得)"
    assert 4 in chinese_tones, "should have tone 4 (更/高)"
    print(f"  [PASS] mixed tones: {tones}")


def test_empty_input():
    """空字符串 → 返回默认聚合值 {fluidity_score: 0}"""
    print("\n[TEST] empty input")
    result = analyse_lyric_tones([])
    assert result["stats"]["overall_fluidity_score"] == 0.0
    assert result["stats"]["avg_entropy"] == 0.0
    assert result["stats"]["dominant_pattern"] == "N/A"
    print(f"  [PASS] empty input handled: fluidity={result['stats']['overall_fluidity_score']}")


def test_feedback_generation():
    """确保 generate_tonal_feedback 至少产生一条有意义的建议"""
    print("\n[TEST] feedback generation")
    # 全阴平句子应触发单调建议
    lines = ["天天天天天空空空空"]
    result = analyse_lyric_tones(lines)
    assert len(result["feedback"]) > 0, "should have at least one feedback"
    print(f"  [PASS] feedback generated ({len(result['feedback'])} items)")
    for fb in result["feedback"]:
        print(f"    - {fb}")

    # 整体熵高应有正面建议
    lines2 = ["飞得更高", "天空很蓝", "心情很爽"]
    result2 = analyse_lyric_tones(lines2)
    print(f"  [PASS] diverse feedback: {result2['feedback']}")


def test_integration_with_core():
    """RapFlowSkill.run() 的输出中包含 tonal_analysis 键且结构正确"""
    print("\n[TEST] integration with RapFlowSkill")
    skill = RapFlowSkill()
    lyrics = "小镇的男孩儿现在做着嘻哈这门生意\n我们不姓谢但也是老板儿"
    result = skill.run({
        "text": lyrics,
        "analyze_flow": False,
        "detect_multi_rhyme": False,
        "analyze_tonal": True,
    })
    assert "tonal_analysis" in result, "tonal_analysis key missing from output"
    tonal = result["tonal_analysis"]
    assert tonal is not None
    assert "lines" in tonal
    assert "stats" in tonal
    assert "feedback" in tonal
    assert isinstance(tonal["lines"], list)
    assert len(tonal["lines"]) == 2
    for line_data in tonal["lines"]:
        assert "tone_sequence" in line_data
        assert "pattern_type" in line_data
        assert "tonal_entropy" in line_data
        assert "rising_ratio" in line_data
        assert "falling_ratio" in line_data
    print(f"  [PASS] tonal_analysis in output: {tonal['stats']}")


def test_tonal_disable():
    """analyze_tonal=False 时 tonal_analysis 为 None"""
    print("\n[TEST] tonal analysis disabled")
    skill = RapFlowSkill()
    result = skill.run({
        "text": "测试歌词",
        "analyze_tonal": False,
    })
    assert result["tonal_analysis"] is None
    print("  [PASS] tonal_analysis is None when disabled")


def test_tonal_entropy_range():
    """验证香农熵值在合理范围内"""
    print("\n[TEST] tonal entropy range")
    import math
    max_entropy = math.log2(5)

    # 全同调 → 熵 = 0
    result = analyse_lyric_tones(["天天天天"])
    assert result["lines"][0]["tonal_entropy"] == 0.0

    # 多样调 → 熵 > 0
    result2 = analyse_lyric_tones(["飞得更高"])
    assert result2["lines"][0]["tonal_entropy"] > 0.0
    assert result2["lines"][0]["tonal_entropy"] <= max_entropy

    print(f"  [PASS] entropy in range [0, {max_entropy:.4f}]")


def test_transition_ratios():
    """验证升降调比例计算"""
    print("\n[TEST] transition ratios")
    # 全升调序列 1→2→3→4
    tones = [1, 2, 3, 4]
    rising, falling = _calc_transition_ratios(tones)
    assert rising == 1.0, f"Expected rising=1.0, got {rising}"
    assert falling == 0.0, f"Expected falling=0.0, got {falling}"

    # 全降调序列 4→3→2→1
    tones2 = [4, 3, 2, 1]
    rising2, falling2 = _calc_transition_ratios(tones2)
    assert rising2 == 0.0
    assert falling2 == 1.0

    print(f"  [PASS] rising={rising}, falling={falling}")


def test_single_char_line():
    """单字行不崩溃"""
    print("\n[TEST] single char line")
    result = analyse_lyric_tones(["天"])
    assert len(result["lines"]) == 1
    assert result["lines"][0]["tone_sequence"] == [1]
    print(f"  [PASS] single char handled: {result['lines'][0]}")


def test_all_nonchinese():
    """纯英文/数字行，无汉字"""
    print("\n[TEST] all non-Chinese line")
    result = analyse_lyric_tones(["hello world 123"])
    assert len(result["lines"]) == 1
    assert result["lines"][0]["pattern_type"] in ("wave", "flat", "alternating")
    assert result["lines"][0]["tonal_entropy"] == 0.0
    print(f"  [PASS] non-Chinese handled: {result['lines'][0]}")


def test_function_schema_has_analyze_tonal():
    """function schema 包含 analyze_tonal 参数"""
    print("\n[TEST] function schema has analyze_tonal")
    skill = RapFlowSkill()
    schema = skill.get_function_schema()
    props = schema["parameters"]["properties"]
    assert "analyze_tonal" in props
    assert props["analyze_tonal"]["type"] == "boolean"
    print(f"  [PASS] analyze_tonal in schema: {props['analyze_tonal']}")


def test_json_serialization_with_tonal():
    """含 tonal_analysis 的输出可正常 JSON 序列化"""
    print("\n[TEST] JSON serialization with tonal")
    skill = RapFlowSkill()
    result = skill.run({
        "text": "测试歌词\n第二行",
        "analyze_tonal": True,
    })
    json_str = json.dumps(result, ensure_ascii=False)
    parsed = json.loads(json_str)
    assert "tonal_analysis" in parsed
    assert parsed["tonal_analysis"] is not None
    print(f"  [PASS] JSON serialization OK ({len(json_str)} bytes)")


def main():
    """Run all tonal tests"""
    sep = "=" * 60
    print(sep)
    print("RapFlow-Skill v1.5.0 Tonal Analysis Tests")
    print(sep)

    tests = [
        test_flat_tone,
        test_alternating_tone,
        test_wave_tone,
        test_mixed_nonchinese,
        test_empty_input,
        test_feedback_generation,
        test_integration_with_core,
        test_tonal_disable,
        test_tonal_entropy_range,
        test_transition_ratios,
        test_single_char_line,
        test_all_nonchinese,
        test_function_schema_has_analyze_tonal,
        test_json_serialization_with_tonal,
    ]

    passed = 0
    failed = 0
    first_error = None

    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {e}")
            failed += 1
            if first_error is None:
                first_error = e
        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            if first_error is None:
                first_error = e

    print()
    print(sep)
    print(f"Results: {passed} passed, {failed} failed")
    print(sep)

    return failed == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
