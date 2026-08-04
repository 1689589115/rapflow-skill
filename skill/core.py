"""
Skill主入口 - 为LLM Function Call提供统一接口
"""

import json
from typing import Dict, Any
from .schemas import RapFlowInput, RapFlowOutput, LineResult, RhymeUnit
from .utils import clean_lyric, split_lines
from .rhyme_analyzer import RhymeAnalyzer


class RapFlowSkill:
    """
    RapFlow Skill - 中文说唱文本分析技能
    
    功能：
    - 押韵检测
    - 韵母提取
    - 多押识别
    - 换气标记
    - 押韵密度统计
    """
    
    def __init__(self):
        """初始化Skill"""
        self.name = "rapflow_skill"
        self.description = """
        中文说唱文本分析工具，提供押韵检测、韵母提取、多押识别、换气标记等功能。
        分析说唱歌词的押韵结构，输出结构化JSON数据，支持大模型Function Call调用。
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
                    }
                },
                "required": ["text"]
            }
        }
    
    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        统一对外入口
        
        Args:
            params: 参数字典，包含 text, mode, mark_breath, max_rhyme_level
            
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
            
            # 执行分析
            results, avg_density, summary = analyzer.analyse_lyric(
                lines,
                mark_breath=input_model.mark_breath
            )
            
            # 构建输出
            output = RapFlowOutput(
                success=True,
                mode=input_model.mode,
                total_lines=len(lines),
                avg_rhyme_density=avg_density,
                lines_result=results,
                summary=summary
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
                "summary": f"分析失败: {str(e)}"
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
    test_lyrics = """
    我唱歌的flow 非常优秀
    这个beat让我忍不住抖
    我的韵脚像子弹一样透
    每一个字都充满力量够
    """
    
    result = skill.run({
        "text": test_lyrics,
        "mode": "auto",
        "mark_breath": True,
        "max_rhyme_level": 4
    })
    
    print(json.dumps(result, ensure_ascii=False, indent=2))