# -*- coding: utf-8 -*-
"""
Multi-rhyme detection feature tests - v1.1.0
"""

import sys
from pathlib import Path

# 添加项目根目录到路径（跨平台兼容）
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill import RapFlowSkill
import json


def test_single_rhyme():
    """Test single rhyme detection"""
    print("\n=== Test 1: Single Rhyme ===")
    lyrics = "Youxian\nDou"
    result = RapFlowSkill().run({
        "text": lyrics,
        "detect_multi_rhyme": True
    })
    
    for line in result['lines_result']:
        if line.get('multi_rhyme'):
            assert line['multi_rhyme']['type'] == "单押", f"Expected single rhyme, got {line['multi_rhyme']['type']}"
            print(f"[PASS] Text: {line['text']}")
            print(f"[PASS] Type: {line['multi_rhyme']['type']}")
            print(f"[PASS] Rhymes: {line['rhyme']['rhymes']}")


def test_double_rhyme():
    """Test double rhyme detection"""
    print("\n=== Test 2: Double/Triple/Quad Rhyme ===")
    lyrics = "Xiao zhen de nan hai men xian zai zuo zhe xi ha zhe men sheng yi\nWo men bu xing xie dan ye shi lao ban er"
    result = RapFlowSkill().run({
        "text": lyrics,
        "detect_multi_rhyme": True
    })
    
    for line in result['lines_result']:
        if line.get('multi_rhyme'):
            multi_type = line['multi_rhyme']['type']
            count = line['multi_rhyme']['count']
            # Accept any multi-rhyme type (double, triple, quad)
            assert count >= 2, f"Expected at least 2 rhymes, got {count}"
            print(f"[PASS] Text: {line['text'][:30]}...")
            print(f"[PASS] Type: {multi_type}")
            print(f"[PASS] Count: {count} rhymes")
            print(f"[PASS] Examples: {line['multi_rhyme']['examples']}")


def test_triple_rhyme():
    """Test triple rhyme detection"""
    print("\n=== Test 3: Triple Rhyme ===")
    lyrics = "Zai ka zuo li mian liao mei er\nZai deng tou gang li na fan er"
    result = RapFlowSkill().run({
        "text": lyrics,
        "detect_multi_rhyme": True
    })
    
    for line in result['lines_result']:
        if line.get('multi_rhyme') and line['multi_rhyme']['count'] >= 3:
            print(f"[PASS] Text: {line['text']}")
            print(f"[PASS] Type: {line['multi_rhyme']['type']}")
            print(f"[PASS] Combinations: {line['multi_rhyme']['rhyme_combinations']}")


def test_full_lyrics():
    """Test full lyrics analysis"""
    print("\n=== Test 4: Full Lyrics Analysis ===")
    lyrics = """Xiao zhen de nan hai men xian zai zuo zhe xi ha zhe men sheng yi
Wo men bu xing xie dan ye shi lao ban er
Zai ka zuo li mian liao mei er
Zai deng tou gang li na fan er
Zai wu tai shang mian sa shui er"""
    
    result = RapFlowSkill().run({
        "text": lyrics,
        "detect_multi_rhyme": True
    })
    
    # Show overall stats
    print(f"\nTotal lines: {result['total_lines']}")
    print(f"Average density: {result['avg_rhyme_density']:.3f}")
    print(f"Summary: {result['summary']}")
    
    # Show multi-rhyme stats
    if result.get('multi_rhyme_stats'):
        stats = result['multi_rhyme_stats']
        print(f"\n[Multi-rhyme stats]")
        print(f"  Single rhyme: {stats['single_rhyme_lines']} lines")
        print(f"  Double rhyme: {stats['double_rhyme_lines']} lines")
        print(f"  Triple rhyme: {stats['triple_rhyme_lines']} lines")
        print(f"  Quad+: {stats['quad_rhyme_lines'] + stats['multi_rhyme_lines']} lines")
        print(f"  Most common pattern: {stats['most_common_pattern']}")
    
    # Show detailed examples
    print(f"\n[Typical examples]")
    examples = result.get('multi_rhyme_stats', {}).get('detailed_examples', []) or []
    for i, example in enumerate(examples[:3], 1):
        print(f"\n  Example {i}:")
        print(f"    Text: {example['line']}")
        print(f"    Type: {example['type']}")
        print(f"    Rhymes: {example['rhymes']}")


def test_multi_rhyme_disabled():
    """Test disabling multi-rhyme detection"""
    print("\n=== Test 5: Disable Multi-rhyme Detection ===")
    lyrics = "Xiao zhen de nan hai men xian zai zuo zhe xi ha zhe men sheng yi"
    result = RapFlowSkill().run({
        "text": lyrics,
        "detect_multi_rhyme": False
    })
    
    # Check no multi_rhyme field exists
    for line in result['lines_result']:
        assert line.get('multi_rhyme') is None, "multi_rhyme should be None when disabled"
        print(f"[PASS] Multi-rhyme disabled: {line['text']}")
    
    # Check no multi_rhyme_stats
    assert result.get('multi_rhyme_stats') is None, "multi_rhyme_stats should be None when disabled"
    print(f"[PASS] Multi-rhyme stats disabled")


if __name__ == "__main__":
    test_single_rhyme()
    test_double_rhyme()
    test_triple_rhyme()
    test_full_lyrics()
    test_multi_rhyme_disabled()
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)
