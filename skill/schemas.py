"""
Pydantic v2 参数模型定义 - v1.5.0
定义输入输出数据结构，严格匹配 OpenAI Function Call 格式
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict


class RhymeUnit(BaseModel):
    """单行押韵单元"""
    rhymes: List[str] = Field(description="该行中识别出的韵母列表")
    level: int = Field(description="押韵等级（1-6，数字越大越丰富）")
    density: float = Field(description="押韵密度，韵脚数量与行长的比例")


class MultiRhymeInfo(BaseModel):
    """多押分析结果"""
    type: str = Field(description="押韵类型：单押/双押/三押/四押/五押+")
    count: int = Field(description="该行的韵母组合数")
    rhyme_combinations: List[Dict[str, int]] = Field(
        description="韵母组合详情，如 [{'ang': 2}, {'i': 3}] 表示ang出现2次，i出现3次"
    )
    examples: List[str] = Field(description="展示多押的具体歌词片段")


class LineResult(BaseModel):
    """单行分析结果"""
    line_index: int = Field(description="行索引（从0开始）")
    text: str = Field(description="清洗后的歌词文本")
    rhyme: Optional[RhymeUnit] = Field(default=None, description="押韵信息")
    multi_rhyme: Optional[MultiRhymeInfo] = Field(default=None, description="多押分析")
    breath_mark: Optional[str] = Field(default=None, description="带换气标记的文本")


class FlowInfo(BaseModel):
    """Flow节奏分析结果"""
    style: str = Field(description="Flow风格：Boom Bap/Trap/Drill/Chopper/Melodic")
    confidence: float = Field(description="置信度（0-1）")
    details: str = Field(description="分析详情")


class TonalLineResult(BaseModel):
    """单行声调分析结果"""
    line_index: int = Field(description="行索引（从0开始）")
    tone_sequence: List[int] = Field(description="该行所有字的声调序列（-1=非汉字）")
    pattern_type: str = Field(description="声调模式类型：flat/alternating/wave")
    tonal_entropy: float = Field(description="香农熵，度量声调多样性，range [0, log2(5)]")
    rising_ratio: float = Field(description="升调转移比例")
    falling_ratio: float = Field(description="降调转移比例")


class TonalStats(BaseModel):
    """段落级声调统计"""
    avg_entropy: float = Field(description="整段平均声调熵")
    dominant_pattern: str = Field(description="出现最多的 pattern_type")
    overall_fluidity_score: float = Field(description="综合流畅度评分 [0, 100]")


class TonalAnalysisResult(BaseModel):
    """完整声调分析结果"""
    lines: List[TonalLineResult] = Field(description="每行声调分析结果")
    stats: TonalStats = Field(description="段落级统计")
    feedback: List[str] = Field(description="自然语言质量评估建议")


class RapFlowInput(BaseModel):
    """输入参数模型 - v1.5.0"""
    text: str = Field(description="说唱歌词文本")
    mode: str = Field(default="auto", description="分析模式：auto/strict/casual")
    mark_breath: bool = Field(default=True, description="是否添加换气标记")
    max_rhyme_level: int = Field(default=4, ge=1, le=6, description="最大押韵等级")
    detect_multi_rhyme: bool = Field(default=True, description="是否检测多押")
    analyze_flow: bool = Field(default=True, description="是否进行Flow节奏分析")
    analyze_tonal: bool = Field(default=True, description="是否进行声调搭配分析")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "小镇的男孩儿现在做着嘻哈这门生意\n我们不姓谢但也是老板儿",
                "mode": "auto",
                "mark_breath": True,
                "max_rhyme_level": 4,
                "detect_multi_rhyme": True
            }
        }
    )


class MultiRhymeStats(BaseModel):
    """多押统计信息"""
    total_lines: int = Field(description="总行数")
    single_rhyme_lines: int = Field(description="单押行数")
    double_rhyme_lines: int = Field(description="双押行数")
    triple_rhyme_lines: int = Field(description="三押行数")
    quad_rhyme_lines: int = Field(description="四押行数")
    multi_rhyme_lines: int = Field(description="五押及以上行数")
    most_common_pattern: str = Field(description="最常见的押韵模式")
    detailed_examples: List[Dict] = Field(description="详细示例")


class RapFlowOutput(BaseModel):
    """输出结果模型 - v1.5.0"""
    success: bool = Field(description="是否成功")
    mode: str = Field(description="分析模式")
    total_lines: int = Field(description="总行数")
    avg_rhyme_density: float = Field(description="平均押韵密度")
    lines_result: List[LineResult] = Field(description="每行分析结果")
    summary: str = Field(description="分析总结文本")
    multi_rhyme_stats: Optional[MultiRhymeStats] = Field(default=None, description="多押统计信息")
    flow: Optional[FlowInfo] = Field(default=None, description="Flow节奏分析结果")
    tonal_analysis: Optional[TonalAnalysisResult] = Field(default=None, description="声调搭配分析结果")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "mode": "auto",
                "total_lines": 2,
                "avg_rhyme_density": 0.5,
                "lines_result": [
                    {
                        "line_index": 0,
                        "text": "小镇的男孩儿现在做着嘻哈这门生意",
                        "rhyme": {"rhymes": ["ing", "un", "ie", "uo", "ai"], "level": 3, "density": 0.312},
                        "multi_rhyme": {
                            "type": "双押",
                            "count": 2,
                            "rhyme_combinations": [{"ai": 1}, {"ing": 1}],
                            "examples": ["生意(yi)", "儿(er)"]
                        },
                        "breath_mark": "小镇的男孩儿 / 现在做着嘻哈 / 这门生意"
                    }
                ],
                "summary": "共2行，平均押韵密度0.5，检测到双押结构",
                "multi_rhyme_stats": {
                    "total_lines": 2,
                    "single_rhyme_lines": 0,
                    "double_rhyme_lines": 2,
                    "triple_rhyme_lines": 0,
                    "quad_rhyme_lines": 0,
                    "multi_rhyme_lines": 0,
                    "most_common_pattern": "双押",
                    "detailed_examples": []
                }
            }
        }
    )
