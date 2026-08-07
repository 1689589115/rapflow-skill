# -*- coding: utf-8 -*-
"""
New tests for v1.5.0: Flow analysis, normalization, encoding safety
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from skill import RapFlowSkill, insert_breath_mark
from skill.rhyme_analyzer import RhymeNormalizer
from skill.flow_analyzer import analyze_flow


def test_breath_mark_dedup():
    """Test that insert_breath_mark from utils is used (deduped)"""
    print("\n[TEST] breath_mark deduplication")
    text = "这是一个测试歌词用来验证换气标记是否正常工作"
    result = insert_breath_mark(text, interval=8)
    # Should insert "/" after 8 Chinese chars
    assert " / " in result, "breath mark should be inserted"
    print(f"  [PASS] breath_mark result: {result}")


def test_rhyme_normalization():
    """Test rhyme normalization reduces false positives"""
    print("\n[TEST] rhyme normalization")
    # Normalize韵母（finals），不是完整拼音
    assert RhymeNormalizer.normalize("ing") == "in"
    assert RhymeNormalizer.normalize("iong") == "in"
    assert RhymeNormalizer.normalize("iang") == "ian"
    assert RhymeNormalizer.normalize("uang") == "uan"
    assert RhymeNormalizer.normalize("eng") == "en"
    assert RhymeNormalizer.normalize("ong") == "en"
    assert RhymeNormalizer.normalize("iou") == "ou"
    assert RhymeNormalizer.normalize("uei") == "ui"
    assert RhymeNormalizer.normalize("uen") == "un"
    # 不变韵母
    assert RhymeNormalizer.normalize("a") == "a"
    assert RhymeNormalizer.normalize("an") == "an"
    # 未知韵母保持原样
    assert RhymeNormalizer.normalize("xyz") == "xyz"
    print("  [PASS] all normalization rules correct")


def test_flow_analysis_empty():
    """Test flow analysis with empty input"""
    print("\n[TEST] flow analysis - empty input")
    result = analyze_flow([], [])
    assert result["style"] == "Unknown"
    assert result["confidence"] == 0.0
    print(f"  [PASS] empty input handled: {result['style']}")


def test_flow_analysis_short():
    """Test flow analysis with short lyrics"""
    print("\n[TEST] flow analysis - short lyrics")
    lines = ["测试歌词", "第二行"]
    densities = [0.5, 0.5]
    result = analyze_flow(lines, densities)
    assert "style" in result
    assert 0 <= result["confidence"] <= 1
    print(f"  [PASS] short lyrics flow: {result['style']} (conf={result['confidence']})")


def test_flow_analysis_chopper():
    """Test flow analysis with high-density (Chopper-like) lyrics"""
    print("\n[TEST] flow analysis - chopper style")
    # Chopper style: >=14 syllables per line
    lines = [
        "快嘴flow像子弹穿透所有的障碍现在",
        "密集韵脚让每一个字都充满力量和",
        "速度和控制完美结合创造震撼的场面",
        "这就是chopper风格让所有人为之疯狂",
    ]
    densities = [0.9, 0.88, 0.85, 0.92]
    result = analyze_flow(lines, densities)
    assert result["style"] == "Chopper"
    assert result["confidence"] >= 0.9
    print(f"  [PASS] chopper detection: {result['style']} (conf={result['confidence']})")


def test_rapflow_output_has_flow():
    """Test that RapFlowOutput includes flow field"""
    print("\n[TEST] RapFlowOutput has flow field")
    skill = RapFlowSkill()
    result = skill.run({
        "text": "测试歌词\n第二行",
        "analyze_flow": True
    })
    assert "flow" in result, "flow field should be in result"
    if result["flow"]:
        assert "style" in result["flow"]
        assert "confidence" in result["flow"]
        assert "details" in result["flow"]
    print(f"  [PASS] flow field present: {result.get('flow', {}).get('style', 'N/A')}")


def test_rapflow_output_without_flow():
    """Test that RapFlowOutput without flow analysis still works"""
    print("\n[TEST] RapFlowOutput without flow analysis")
    skill = RapFlowSkill()
    result = skill.run({
        "text": "测试歌词\n第二行",
        "analyze_flow": False
    })
    assert "flow" in result
    assert result["flow"] is None
    print("  [PASS] flow=None when analyze_flow=False")


def test_json_serialization_with_flow():
    """Test JSON serialization including flow field"""
    print("\n[TEST] JSON serialization with flow")
    skill = RapFlowSkill()
    result = skill.run({
        "text": "测试歌词\n第二行",
        "analyze_flow": True
    })
    json_str = json.dumps(result, ensure_ascii=False, indent=2)
    parsed = json.loads(json_str)
    assert "success" in parsed
    assert "flow" in parsed
    print(f"  [PASS] JSON serialization OK ({len(json_str)} bytes)")


def test_function_schema_has_analyze_flow():
    """Test that function schema includes analyze_flow parameter"""
    print("\n[TEST] function schema has analyze_flow")
    skill = RapFlowSkill()
    schema = skill.get_function_schema()
    props = schema["parameters"]["properties"]
    assert "analyze_flow" in props, "analyze_flow should be in schema"
    assert props["analyze_flow"]["type"] == "boolean"
    print(f"  [PASS] analyze_flow in schema: {props['analyze_flow']}")


def test_encoding_safety():
    """Test that output can be safely serialized (no encoding issues)"""
    print("\n[TEST] encoding safety")
    skill = RapFlowSkill()
    result = skill.run({
        "text": "测试歌词",
        "detect_multi_rhyme": True,
        "analyze_flow": True,
    })
    # Should not raise any encoding error
    json_str = json.dumps(result, ensure_ascii=False)
    assert isinstance(json_str, str)
    assert len(json_str) > 0
    print(f"  [PASS] encoding safe, output length: {len(json_str)}")


def test_all_modes_with_flow():
    """Test all modes work with flow analysis enabled"""
    print("\n[TEST] all modes with flow analysis")
    skill = RapFlowSkill()
    lyrics = "测试歌词\n第二行"
    for m in ["auto", "strict", "casual"]:
        r = skill.run({"text": lyrics, "mode": m, "analyze_flow": True})
        assert r["success"], f"{m} mode failed"
        assert r["flow"] is not None, f"{m} mode should have flow"
        print(f"  [PASS] mode={m}, flow={r['flow']['style']}")


def test_flow_boom_bap():
    """Test Boom Bap style detection"""
    print("\n[TEST] flow analysis - boom bap style")
    lines = ["小镇的男孩儿现在做着嘻哈", "我们不姓谢但也是老板儿", "在卡座里面撩妹儿"]
    densities = [0.3, 0.3, 0.3]
    result = analyze_flow(lines, densities)
    assert result["style"] == "Boom Bap"
    print(f"  [PASS] boom bap detection: {result['style']} (conf={result['confidence']})")


def test_flow_trap():
    """Test Trap style detection (repetitive)"""
    print("\n[TEST] flow analysis - trap style")
    lines = ["我的flow重复重复重复重复", "我的flow重复重复重复重复"]
    densities = [0.5, 0.5]
    result = analyze_flow(lines, densities)
    assert result["style"] == "Trap"
    print(f"  [PASS] trap detection: {result['style']} (conf={result['confidence']})")


def test_import_all_modules():
    """Test that all new modules can be imported"""
    print("\n[TEST] import all modules")
    from skill.flow_analyzer import analyze_flow, _count_chinese_syllables
    from skill.utils import insert_breath_mark, _safe_print
    assert callable(analyze_flow)
    assert callable(insert_breath_mark)
    assert callable(_count_chinese_syllables)
    print(f"  [PASS] flow_analyzer: analyze_flow OK")
    print(f"  [PASS] utils: insert_breath_mark, _safe_print OK")


def main():
    """Run all new tests"""
    sep = "=" * 60
    print(sep)
    print("RapFlow-Skill v1.5.0 New Tests")
    print(sep)

    tests = [
        test_import_all_modules,
        test_breath_mark_dedup,
        test_rhyme_normalization,
        test_flow_analysis_empty,
        test_flow_analysis_short,
        test_flow_analysis_chopper,
        test_rapflow_output_has_flow,
        test_rapflow_output_without_flow,
        test_json_serialization_with_flow,
        test_function_schema_has_analyze_flow,
        test_encoding_safety,
        test_all_modes_with_flow,
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
