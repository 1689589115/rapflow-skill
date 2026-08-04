"""
Basic unit tests for rapflow-skill
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_import():
    """Test that all modules can be imported"""
    print("\n[TEST] module imports")
    from skill.core import RapFlowSkill
    from skill.schemas import RapFlowInput, RapFlowOutput, LineResult, RhymeUnit
    from skill.utils import clean_lyric, split_lines
    from skill.rhyme_analyzer import RhymeAnalyzer
    print("  [PASS] all imports OK")


def test_clean_lyric():
    """Test lyric cleaning"""
    print("\n[TEST] clean_lyric")
    from skill.utils import clean_lyric
    
    text = "这是一个(括号内容)测试"
    result = clean_lyric(text)
    assert "括号内容" not in result, "brackets should be removed"
    print(f"  [PASS] remove brackets -> '{result}'")
    
    text = "汉字保留"
    result = clean_lyric(text)
    assert len(result.strip()) > 0, "chinese chars should remain"
    print(f"  [PASS] keep chinese chars -> '{result}'")


def test_split_lines():
    """Test line splitting"""
    print("\n[TEST] split_lines")
    from skill.utils import split_lines
    
    text = "line1\nline2\rline3\tline4"
    lines = split_lines(text)
    assert len(lines) == 4, f"expected 4 lines, got {len(lines)}"
    assert lines[0] == "line1", f"first line mismatch: {lines[0]}"
    print(f"  [PASS] split multiline -> {len(lines)} lines")
    
    # Empty line filter
    text = "a\n\n\nb"
    lines = split_lines(text)
    assert len(lines) == 2, f"empty filter failed, got {len(lines)}"
    print(f"  [PASS] filter empty lines -> {len(lines)} lines")


def test_rhyme_analyzer():
    """Test rhyme analysis"""
    print("\n[TEST] rhyme analyzer")
    from skill.rhyme_analyzer import RhymeAnalyzer
    
    analyzer = RhymeAnalyzer()
    line = "我唱歌的flow 非常优秀"
    rhyme_unit = analyzer.calc_line_rhyme(line, [])
    assert rhyme_unit is not None, "rhyme unit must not be None"
    print(f"  [PASS] single line analyzed (level={rhyme_unit.level}, rhymes={rhyme_unit.rhymes})")
    
    # Multi-line
    lines_list = ["我唱歌的flow 非常优秀", "这个beat让我忍不住抖"]
    results, avg_d, summary = analyzer.analyse_lyric(lines_list, mark_breath=False)
    assert len(results) == 2, f"expected 2 results, got {len(results)}"
    assert avg_d >= 0, "avg density negative"
    print(f"  [PASS] multi line analyzed (density={avg_d:.3f})")


def test_rapflow_skill():
    """Test main Skill entry point"""
    print("\n[TEST] RapFlowSkill main entry")
    from skill.core import RapFlowSkill
    
    skill = RapFlowSkill()
    lyrics = "我唱歌的flow 非常优秀\n这个beat让我忍不住抖"
    result = skill.run({
        "text": lyrics,
        "mode": "auto",
        "mark_breath": True,
        "max_rhyme_level": 4
    })
    assert result["success"] == True, f"should succeed, error: {result.get('summary')}"
    assert result["total_lines"] == 2, f"lines={result['total_lines']}"
    assert len(result["lines_result"]) == 2
    print(f"  [PASS] basic call success (lines={result['total_lines']})")
    
    schema = skill.get_function_schema()
    assert schema["name"] == "rapflow_skill"
    assert "parameters" in schema
    print(f"  [PASS] function schema (name={schema['name']})")


def test_all_modes():
    """Test different analysis modes"""
    print("\n[TEST] analysis modes")
    from skill.core import RapFlowSkill
    
    skill = RapFlowSkill()
    lyrics = "测试歌词\n第二行"
    for m in ["auto", "strict", "casual"]:
        r = skill.run({"text": lyrics, "mode": m})
        assert r["success"], f"{m} mode failed"
        print(f"  [PASS] mode={m}")


def test_json_output():
    """Test JSON output structure"""
    print("\n[TEST] JSON output structure")
    from skill.core import RapFlowSkill
    
    skill = RapFlowSkill()
    lyrics = "测试文本"
    result = skill.run({"text": lyrics})
    
    # Verify it serializes to JSON without errors
    json_str = json.dumps(result, ensure_ascii=False, indent=2)
    parsed = json.loads(json_str)
    assert "success" in parsed
    assert "lines_result" in parsed
    assert "summary" in parsed
    print(f"  [PASS] JSON serialization OK ({len(json_str)} bytes)")
    print(f"  Output preview:")
    print(json_str[:500])


def main():
    """Run all tests"""
    sep = "=" * 60
    print(sep)
    print("RapFlow-Skill Tests")
    print(sep)
    
    tests = [
        test_import,
        test_clean_lyric,
        test_split_lines,
        test_rhyme_analyzer,
        test_rapflow_skill,
        test_all_modes,
        test_json_output,
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
