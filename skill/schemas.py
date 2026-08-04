"""
Pydantic v2 参数模型定义
定义输入输出数据结构，严格匹配 OpenAI Function Call 格式
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class RhymeUnit(BaseModel):
    """单行押韵单元"""
    rhymes: List[str] = Field(description="该行中识别出的韵母列表")
    level: int = Field(description="押韵等级（1-6，数字越大越丰富）")
    density: float = Field(description="押韵密度，韵脚数量与行长的比例")


class LineResult(BaseModel):
    """单行分析结果"""
    line_index: int = Field(description="行索引（从0开始）")
    text: str = Field(description="清洗后的歌词文本")
    rhyme: Optional[RhymeUnit] = Field(default=None, description="押韵信息")
    breath_mark: Optional[str] = Field(default=None, description="带换气标记的文本")


class RapFlowInput(BaseModel):
    """输入参数模型"""
    text: str = Field(description="说唱歌词文本")
    mode: str = Field(default="auto", description="分析模式：auto/strict/casual")
    mark_breath: bool = Field(default=True, description="是否添加换气标记")
    max_rhyme_level: int = Field(default=4, ge=1, le=6, description="最大押韵等级")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "我唱歌的flow 非常优秀\n这个beat让我忍不住抖",
                "mode": "auto",
                "mark_breath": True,
                "max_rhyme_level": 4
            }
        }


class RapFlowOutput(BaseModel):
    """输出结果模型"""
    success: bool = Field(description="是否成功")
    mode: str = Field(description="分析模式")
    total_lines: int = Field(description="总行数")
    avg_rhyme_density: float = Field(description="平均押韵密度")
    lines_result: List[LineResult] = Field(description="每行分析结果")
    summary: str = Field(description="分析总结文本")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "mode": "auto",
                "total_lines": 2,
                "avg_rhyme_density": 0.8,
                "lines_result": [
                    {
                        "line_index": 0,
                        "text": "我唱歌的flow 非常优秀",
                        "rhyme": {"rhymes": ["iu"], "level": 1, "density": 0.5},
                        "breath_mark": "我唱歌的flow / 非常优秀"
                    }
                ],
                "summary": "共2行，平均押韵密度0.8"
            }
        }
    