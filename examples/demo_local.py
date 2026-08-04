"""
本地直接调用示例
演示如何使用RapFlow-Skill进行说唱歌词分析
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill import RapFlowSkill


def main():
    """主函数"""
    # 创建Skill实例
    skill = RapFlowSkill()
    
    # 示例说唱歌词
    lyrics = """
    我唱歌的flow 非常优秀
    这个beat让我忍不住抖
    我的韵脚像子弹一样透
    每一个字都充满力量够
    不管多远的路我都要走
    不管多难的词我都能吼
    音乐是我的灵魂出口
    让我自由飞翔在天空
    """
    
    # 调用分析
    result = skill.run({
        "text": lyrics,
        "mode": "auto",
        "mark_breath": True,
        "max_rhyme_level": 4
    })
    
    # 打印结果
    print("=" * 60)
    print("RapFlow-Skill 分析结果")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 显示每行分析
    print("\n" + "=" * 60)
    print("逐行分析详情")
    print("=" * 60)
    
    for line_result in result["lines_result"]:
        print(f"\n第{line_result['line_index'] + 1}行:")
        print(f"  原文: {line_result['text']}")
        if line_result.get('breath_mark'):
            print(f"  换气: {line_result['breath_mark']}")
        if line_result.get('rhyme'):
            rhyme = line_result['rhyme']
            print(f"  韵母: {rhyme['rhymes']}")
            print(f"  等级: {rhyme['level']}")
            print(f"  密度: {rhyme['density']:.3f}")
    
    # 显示总结
    print("\n" + "=" * 60)
    print("分析总结")
    print("=" * 60)
    print(f"总行数: {result['total_lines']}")
    print(f"平均押韵密度: {result['avg_rhyme_density']:.3f}")
    print(f"总结: {result['summary']}")


if __name__ == "__main__":
    main()