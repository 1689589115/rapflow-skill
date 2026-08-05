"""
Skill主入口 - 为LLM Function Call提供统一接口 - v1.1.0增强版
"""

import json
from typing import Dict, Any
from .schemas import RapFlowInput, RapFlowOutput, LineResult, RhymeUnit, MultiRhymeInfo, MultiRhymeStats
from .utils import clean_lyric, split_lines
from .rhyme_analyzer import RhymeAnalyzer


class RapFlowSkill:
    """
    RapFlow Skill - 中文说唱文本分析技能 - v1.1.0
    
    功能：
    - 押韵检测
    - 韵母提取
    - 多押识别（新增）
    - 换气标记
    - 押韵密度统计
    - 多押统计分析（新增）
    """
    
    def __init__(self):
        """初始化Skill"""
        self.name = "rapflow_skill"
        self.description = """
        中文说唱文本分析工具，提供押韵检测、韵母提取、多押识别、换气标记等功能。
        分析说唱歌词的押韵结构，输出结构化JSON数据，支持大模型Function Call调用。
        v1.1.0新增：自动识别单押、双押、三押、四押、五押+结构。
        """
        
        # 内置Function Schema（OpenAI格式）
        self.function_schema = {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "说唱歌词文本"
                    },
                    "mode": {
                        "type": "string",
                        "description": "分析模式：auto（自动）/ strict（严格）/ casual（宽松）",
                        "enum": ["auto", "strict", "casual"]
                    },
                    "mark_breath": {
                        "type": "boolean",
                        "description": "是否添加换气标记"
                    },
                    "max_rhyme_level": {
                        "type": "integer",
                        "description": "最大押韵等级（1-6）",
                        "minimum": 1,
                        "maximum": 6
                    },
                    "detect_multi_rhyme": {
                        "type": "boolean",
                        "description": "是否检测多押（单押/双押/三押/四押/五押+）",
                        "default": True
                    }
                },
                "required": ["text"]
            }
        }
    
    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        统一对外入口
        
        Args:
            params: 参数字典，包含 text, mode, mark_breath, max_rhyme_level, detect_multi_rhyme
            
        Returns:
            分析结果字典（可序列化为JSON）
        """
        try:
            # 参数校验
            input_model = RapFlowInput(**params)
            
            # 清洗文本
            clean_text = clean_lyric(input_model.text)
            
            # 分割行
            lines = split_lines(clean_text)
            
            # 创建分析器
            analyzer = RhymeAnalyzer(
                mode=input_model.mode,
                max_level=input_model.max_rhyme_level
            )
            
            # 执行分析（支持多押检测）
            results, avg_density, summary, multi_stats = analyzer.analyse_lyric(
                lines,
                mark_breath=input_model.mark_breath,
                detect_multi_rhyme=input_model.detect_multi_rhyme
            )
            
            # 构建输出
            output = RapFlowOutput(
                success=True,
                mode=input_model.mode,
                total_lines=len(lines),
                avg_rhyme_density=avg_density,
                lines_result=results,
                summary=summary,
                multi_rhyme_stats=multi_stats
            )
            
            return output.model_dump()
            
        except Exception as e:
            # 返回错误信息
            return {
                "success": False,
                "mode": params.get("mode", "auto"),
                "total_lines": 0,
                "avg_rhyme_density": 0.0,
                "lines_result": [],
                "summary": f"分析失败: {str(e)}",
                "multi_rhyme_stats": None
            }
    
    def get_function_schema(self) -> Dict[str, Any]:
        """
        获取Function Schema（用于LLM工具调用）
        
        Returns:
            OpenAI格式的Function Schema
        """
        return self.function_schema


# 创建单例实例
skill = RapFlowSkill()


if __name__ == "__main__":
    # 测试示例
    test_lyrics = """小镇的男孩儿现在做着嘻哈这门生意
我们不姓谢但也是老板儿
在卡座里面撩妹儿
在头等舱里拿范儿
在舞台上面洒水儿"""
    
    result = skill.run({
        "text": test_lyrics,
        "mode": "auto",
        "mark_breath": True,
        "max_rhyme_level": 4,
        "detect_multi_rhyme": True
    })
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 显示多押统计
    if result.get('multi_rhyme_stats'):
        stats = result['multi_rhyme_stats']
        print("\n" + "=" * 60)
        print("多押统计")
        print("=" * 60)
        print(f"总行数: {stats['total_lines']}")
        print(f"单押: {stats['single_rhyme_lines']}行")
        print(f"双押: {stats['double_rhyme_lines']}行")
        print(f"三押: {stats['triple_rhyme_lines']}行")
        print(f"最常见模式: {stats['most_common_pattern']}")
