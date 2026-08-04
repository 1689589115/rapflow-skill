# RapFlow-Skill

中文说唱文本分析技能，面向LLM Function Call的押韵分析工具。

## 简介

RapFlow-Skill 是一个 Python 技能库，专为大模型工具调用设计，提供中文说唱歌词的结构化分析能力。支持押韵检测、韵母提取、多押识别、换气标记和押韵密度统计，输出标准 JSON 格式，可无缝接入 OpenAI、DeepSeek、豆包等主流大模型的工具调用功能。

## 特性

- **押韵检测**：自动识别中文说唱歌词的押韵模式
- **韵母提取**：基于汉字韵母映射表，提取每行的韵母
- **多押识别**：支持 1-6 押的多押结构分析
- **换气标记**：自动在歌词中插入换气标记 `/`
- **押韵密度**：计算每行和整体的押韵密度
- **Function Call**：标准 OpenAI 格式工具定义，开箱即用
- **兼容性强**：支持 OpenAI、DeepSeek、豆包等主流 LLM

## 环境要求

- Python 3.10+
- 依赖包：
  - pydantic >= 2.8
  - jieba >= 0.42.1

## 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/rapflow-skill.git
cd rapflow-skill

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
快速开始
1. 本地直接调用

from skill import RapFlowSkill

skill = RapFlowSkill()

lyrics = """
我唱歌的flow 非常优秀
这个beat让我忍不住抖
我的韵脚像子弹一样透
每一个字都充满力量够
"""

result = skill.run({
    "text": lyrics,
    "mode": "auto",
    "mark_breath": True,
    "max_rhyme_level": 4
})

print(result)
2. LLM Function Call 接入

from skill import RapFlowSkill
import openai

skill = RapFlowSkill()

# 获取工具定义
tools = [skill.get_function_schema()]

# 发送请求给LLM
messages = [
    {"role": "user", "content": "分析这段歌词的押韵"}
]

# 使用OpenAI API
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

# 处理工具调用
if response.choices[0].message.get('tool_calls'):
    for tool_call in response.choices[0].message.tool_calls:
        arguments = json.loads(tool_call.function.arguments)
        result = skill.run(arguments)
        # 将结果返回给LLM...
参数说明
输入参数
参数	类型	必填	说明
text	str	是	说唱歌词文本
mode	str	否	分析模式：auto/strict/casual，默认 auto
mark_breath	bool	否	是否添加换气标记，默认 True
max_rhyme_level	int	否	最大押韵等级（1-6），默认 4
输出结构

{
  "success": true,
  "mode": "auto",
  "total_lines": 8,
  "avg_rhyme_density": 0.75,
  "lines_result": [
    {
      "line_index": 0,
      "text": "我唱歌的flow 非常优秀",
      "rhyme": {
        "rhymes": ["iu"],
        "level": 2,
        "density": 0.5
      },
      "breath_mark": "我唱歌的flow / 非常优秀"
    }
  ],
  "summary": "共8行，6行有押韵，平均押韵密度0.750，最佳押韵在第1行（等级2）"
}
运行测试

# 运行单元测试
python -m tests.test_basic

# 或
python tests/test_basic.py
运行示例

# 本地调用示例
python examples/demo_local.py

# LLM Function Call 示例
python examples/demo_llm_function_call.py
项目结构

rapflow-skill/
├── skill/
│   ├── __init__.py          # 模块初始化
│   ├── core.py              # Skill主入口
│   ├── rhyme_analyzer.py    # 押韵分析核心算法
│   ├── schemas.py           # Pydantic模型定义
│   └── utils.py             # 文本清洗工具
├── examples/
│   ├── demo_local.py        # 本地调用示例
│   └── demo_llm_function_call.py  # LLM接入示例
├── tests/
│   └── test_basic.py        # 单元测试
├── .gitignore               # Git忽略配置
├── LICENSE                  # MIT许可证
├── README.md                # 项目文档
└── requirements.txt         # 依赖列表
押韵分析逻辑
韵母映射：内置中文汉字韵母映射表，覆盖常见韵母
反向扫描：从行末向前扫描，提取韵脚
等级计算：根据韵母匹配度和出现频率计算押韵等级（1-6）
密度计算：韵脚数量与汉字总数的比值
换气标记：每8个汉字插入一个 / 标记
Roadmap
 支持更多韵母变体
 添加押韵模式可视化
 支持英文押韵分析
 提供Web API接口
 集成更多LLM平台
贡献指南
欢迎提交 Issue 和 Pull Request！

Fork 本仓库
创建特性分支 (git checkout -b feature/AmazingFeature)
提交更改 (git commit -m 'Add some AmazingFeature')
推送到分支 (git push origin feature/AmazingFeature)
开启 Pull Request
License
本项目采用 MIT 许可证 - 详见 LICENSE 文件。

致谢
感谢所有开源贡献者
基于 Pydantic v2 和 jieba 构建


## 本地运行测试方法

### 方法1：安装依赖并运行测试
```bash
# 创建虚拟环境
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行单元测试
python tests/test_basic.py
方法2：运行示例

# 本地调用示例
python examples/demo_local.py

# LLM Function Call 示例
python examples/demo_llm_function_call.py