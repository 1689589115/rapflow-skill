"""
Flow Rhythm Analysis Module - v1.4.0
分析说唱歌词的节奏模式、重音位置和flow复杂度
"""

from typing import Dict, List, Optional, Tuple
from collections import Counter
import re


class FlowAnalyzer:
    """说唱Flow节奏分析器"""
    
    # 常见节奏型特征
    RHYTHM_PATTERNS = {
        'boom_bap': {
            'description': '经典Boom Bap风格，强调第1和第3拍',
            'pattern': [1, 0, 1, 0],  # 重音模式
            'weight': 0.8
        },
        'trap': {
            'description': 'Trap风格，复杂的hi-hat滚动和808 bass',
            'pattern': [1, 0, 0, 1, 0, 1],
            'weight': 0.7
        },
        'drill': {
            'description': 'Drill风格，滑音和切分节奏',
            'pattern': [1, 0, 1, 0, 0, 1],
            'weight': 0.6
        },
        'melodic': {
            'description': '旋律说唱，流畅的韵脚流动',
            'pattern': [1, 1, 0, 1, 0],
            'weight': 0.5
        },
        'chopper': {
            'description': '快速说唱，密集的字词',
            'pattern': [1, 1, 1, 1, 0],
            'weight': 0.9
        }
    }
    
    def __init__(self):
        self.patterns = self.RHYTHM_PATTERNS
    
    def analyze_line_flow(self, line: str) -> Dict:
        """分析单行歌词的Flow模式"""
        # 提取汉字和音节
        chinese_chars = [c for c in line if '\u4e00' <= c <= '\u9fa5']
        
        if not chinese_chars:
            return {
                'stress_pattern': [],
                'beat_count': 0,
                'flow_type': 'unknown',
                'complexity': 'low'
            }
        
        # 计算重音模式
        stress_pattern = self._calculate_stress_pattern(chinese_chars)
        
        # 识别节奏型
        rhythm_type = self._detect_rhythm_type(stress_pattern)
        
        # 计算复杂度
        complexity = self._calculate_complexity(stress_pattern)
        
        # 计算节拍密度
        beat_density = len([s for s in stress_pattern if s == 1]) / max(len(stress_pattern), 1)
        
        return {
            'stress_pattern': stress_pattern,
            'beat_count': sum(stress_pattern),
            'flow_type': rhythm_type,
            'complexity': complexity,
            'beat_density': round(beat_density, 2),
            'syllable_count': len(chinese_chars)
        }
    
    def _calculate_stress_pattern(self, chars: List[str]) -> List[int]:
        """计算重音模式（1=重音, 0=轻音）"""
        pattern = []
        length = len(chars)
        
        # 简单规则：每隔几个字设置重音
        # 根据字节长度和音调模式判断
        for i, char in enumerate(chars):
            # 基础重音：每4个字一个重音点
            if i % 4 == 0:
                pattern.append(1)
            # 句末加重音
            elif i == length - 1:
                pattern.append(1)
            # 中间根据音节复杂度判断
            elif self._is_complex_syllable(char):
                pattern.append(1)
            else:
                pattern.append(0)
        
        return pattern
    
    def _is_complex_syllable(self, char: str) -> bool:
        """判断是否为复杂音节（可能为重音）"""
        # 这里可以扩展为更复杂的规则
        # 暂时使用简单规则：特定部首的字
        complex_radicals = ['口', '言', '心', '手', '足', '金', '木', '水', '火']
        for radical in complex_radicals:
            if radical in char:
                return True
        return False
    
    def _detect_rhythm_type(self, stress_pattern: List[int]) -> str:
        """检测节奏类型"""
        if not stress_pattern:
            return 'unknown'
        
        # 统计重音分布
        ones = sum(stress_pattern)
        zeros = len(stress_pattern) - ones
        ratio = ones / max(len(stress_pattern), 1)
        
        # 根据重音密度判断
        if ratio > 0.7:
            return 'chopper'  # 高速说唱
        elif ratio > 0.5:
            return 'boom_bap'  # 经典boom bap
        elif ratio > 0.3:
            return 'trap'  # Trap风格
        elif ratio > 0.2:
            return 'drill'  # Drill风格
        else:
            return 'melodic'  # 旋律说唱
    
    def _calculate_complexity(self, stress_pattern: List[int]) -> str:
        """计算Flow复杂度"""
        if len(stress_pattern) < 4:
            return 'low'
        
        # 计算重音变化次数
        changes = sum(1 for i in range(1, len(stress_pattern)) 
                     if stress_pattern[i] != stress_pattern[i-1])
        
        change_rate = changes / len(stress_pattern)
        
        if change_rate > 0.6:
            return 'high'
        elif change_rate > 0.4:
            return 'medium'
        else:
            return 'low'
    
    def analyze_paragraph_flow(self, lines: List[str]) -> Dict:
        """分析整段歌词的Flow"""
        results = []
        total_beats = 0
        flow_types = Counter()
        complexities = Counter()
        
        for line in lines:
            analysis = self.analyze_line_flow(line)
            results.append(analysis)
            total_beats += analysis['beat_count']
            flow_types[analysis['flow_type']] += 1
            complexities[analysis['complexity']] += 1
        
        # 确定主要Flow类型
        dominant_flow = flow_types.most_common(1)[0][0] if flow_types else 'unknown'
        
        # 确定主要复杂度
        dominant_complexity = complexities.most_common(1)[0][0] if complexities else 'low'
        
        return {
            'line_results': results,
            'total_beats': total_beats,
            'dominant_flow_type': dominant_flow,
            'dominant_complexity': dominant_complexity,
            'avg_beat_density': round(total_beats / max(len(lines), 1), 2)
        }


# 兼容性函数
def analyze_flow(lyrics: str) -> Dict:
    """分析歌词Flow的主函数"""
    analyzer = FlowAnalyzer()
    
    # 分割成行
    lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
    
    # 分析每行
    results = []
    for line in lines:
        result = analyzer.analyze_line_flow(line)
        results.append({
            'text': line[:50] + '...' if len(line) > 50 else line,
            **result
        })
    
    # 整体分析
    overall = analyzer.analyze_paragraph_flow(lines)
    
    return {
        'success': True,
        'total_lines': len(lines),
        'lines_result': results,
        'overall': overall
    }


if __name__ == "__main__":
    # 测试示例
    test_lyrics = """风很大很冷 心里很空洞
梦醒了以后 什么都变空
天空那么蓝 我的心好酸
时间过得慢 思念好漫长"""
    
    result = analyze_flow(test_lyrics)
    
    print("=" * 70)
    print("RapFlow-Skill v1.4.0 - Flow节奏分析演示")
    print("=" * 70)
    print()
    print(f"总行数: {result['total_lines']}")
    print(f"主要Flow类型: {result['overall']['dominant_flow_type']}")
    print(f"主要复杂度: {result['overall']['dominant_complexity']}")
    print(f"平均节拍密度: {result['overall']['avg_beat_density']}")
    print()
    
    print("逐行分析:")
    print("-" * 70)
    for line_result in result['lines_result']:
        print(f"\n歌词: {line_result['text']}")
        print(f"  重音位置: {line_result['stress_pattern']}")
        print(f"  Flow类型: {line_result['flow_type']}")
        print(f"  复杂度: {line_result['complexity']}")
        print(f"  节拍密度: {line_result['beat_density']}")
