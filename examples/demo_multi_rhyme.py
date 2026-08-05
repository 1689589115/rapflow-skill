"""
多押检测功能演示 - v1.1.0
展示如何识别单押、双押、三押等多押结构
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from skill import RapFlowSkill


def main():
    """主函数"""
    skill = RapFlowSkill()
    
    # 示例歌词（法老 - 事业粉）
    lyrics = """Hook
cruising down street wit my brothers from trenches
小镇的男孩儿现在做着嘻哈这门生意
我们不姓谢但也是老板儿
在卡座里面撩妹儿
在头等舱里拿范儿
在舞台上面洒水儿
No face no case 你抓不住
在成都像活在Hollywood
It's Digi Ghetto Couple Hunnid 的下一步
让嘻哈生意让我变成个大地主"""
    
    print("=" * 80)
    print("RapFlow-Skill v1.1.0 多押检测功能演示")
    print("=" * 80)
    
    # 调用分析（开启多押检测）
    result = skill.run({
        "text": lyrics,
        "mode": "auto",
        "mark_breath": True,
        "max_rhyme_level": 4,
        "detect_multi_rhyme": True  # 开启多押检测
    })
    
    # 输出总体统计
    print(f"\n【总体数据】")
    print(f"  总行数: {result['total_lines']}")
    print(f"  平均押韵密度: {result['avg_rhyme_density']:.3f}")
    print(f"\n{result['summary']}")
    
    # 输出多押统计
    if result.get('multi_rhyme_stats'):
        stats = result['multi_rhyme_stats']
        print("\n" + "=" * 80)
        print("【多押统计】")
        print("=" * 80)
        print(f"  总行数: {stats['total_lines']}")
        print(f"  单押行数: {stats['single_rhyme_lines']}")
        print(f"  双押行数: {stats['double_rhyme_lines']}")
        print(f"  三押行数: {stats['triple_rhyme_lines']}")
        print(f"  四押行数: {stats['quad_rhyme_lines']}")
        print(f"  五押+行数: {stats['multi_rhyme_lines']}")
        print(f"  最常见模式: {stats['most_common_pattern']}")
    
    # 输出逐行详细分析
    print("\n" + "=" * 80)
    print("【逐行押韵分析】")
    print("=" * 80)
    
    for line_result in result['lines_result']:
        if line_result.get('rhyme') and line_result['rhyme']['level'] > 0:
            print(f"\n📍 第 {line_result['line_index'] + 1} 行:")
            
            # 显示歌词
            text = line_result['text']
            print(f"   🎤 歌词: {text}")
            
            # 显示换气标记
            if line_result.get('breath_mark'):
                print(f"   💨 换气: {line_result['breath_mark']}")
            
            # 显示基础押韵信息
            rhyme = line_result['rhyme']
            print(f"   🔤 韵母: {rhyme['rhymes']}")
            print(f"   ⭐ 等级: {rhyme['level']}/6")
            print(f"   📊 密度: {rhyme['density']:.3f}")
            
            # 显示多押信息
            if line_result.get('multi_rhyme'):
                multi = line_result['multi_rhyme']
                print(f"   🎯 多押类型: {multi['type']}")
                
                if multi['rhyme_combinations']:
                    combo_str = ", ".join([f"{k}×{v}" for combo in multi['rhyme_combinations'] for k, v in combo.items()])
                    print(f"   📐 韵母组合: {combo_str}")
                
                if multi['examples']:
                    example_str = " → ".join(multi['examples'])
                    print(f"   💡 示例: {example_str}")
    
    # 输出详细示例
    if result.get('multi_rhyme_stats') and result['multi_rhyme_stats']['detailed_examples']:
        print("\n" + "=" * 80)
        print("【典型多押示例】")
        print("=" * 80)
        
        for i, example in enumerate(result['multi_rhyme_stats']['detailed_examples'][:5], 1):
            print(f"\n  示例{i}: {example['line']}")
            print(f"  类型: {example['type']}")
            print(f"  韵母: {example['rhymes']}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
