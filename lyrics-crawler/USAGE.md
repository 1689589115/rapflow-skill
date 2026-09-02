# RapFlow 使用指南

中文说唱歌词爬虫与分析引擎，支持歌词抓取、清洗、存储、分析和专业解说。

## 快速开始

### 1. 命令行用法

```bash
cd C:\Users\七安\Desktop\rap\lyrics-crawler

# 搜索歌手作品
python cli.py search --artist "Jony J"

# 导出语料到文本文件（自动保存到 data/<歌手名>_corpus.txt）
python cli.py corpus --artist "Jony J"

# 抓取新歌词入库
python cli.py crawl --artist "周杰伦" --song "七里香"

# 从本地文件导入歌词
python cli.py import --artist "你的歌手" --song "你的歌" --file song.txt

# 分析歌词并生成解说
python cli.py analyze --artist "Jony J" --song "奴隶" --source github_dataset

# 生成歌手风格档案
python cli.py profile --artist "Jony J"
```

### 2. 完整分析管道（推荐进阶用户）

```bash
# 一键运行完整分析（含LLM解说）
python scripts/full_pipeline.py --artist "Jony J" --song "奴隶"

# 生成 HTML 可视化报告
python scripts/generate_report.py --artist "Jony J" --song "奴隶"
# 然后在浏览器打开 reports/Jony J_奴隶_report.html
```

### 3. Python API（开发者）

```python
import sys
sys.path.insert(0, r'C:\Users\七安\Desktop\rap\clean-rapflow-skill')
sys.path.insert(0, r'C:\Users\七安\Desktop\rap\lyrics-crawler')

from skill.rhyme_analyzer import RhymeAnalyzer
from src.llm_analyzer import LLMAnalyzer

# 分析单段歌词
lyrics = """他们说年轻人要努力
要多去想点主意"""

# 运行分析
rhyme_result = RhymeAnalyzer().analyse_lyric(lyrics)

# LLM专业解说
llm = LLMAnalyzer()
insight = llm.analyze(lyrics, analysis_result={"rhyme": rhyme_result}, artist="示例歌手", song="示例歌曲")
print(insight)
```

## 数据库规模

- **总歌曲数**: 2,607首
- **歌手数量**: 76位
- **数据来源**: GitHub数据集 + lrc_cx实时抓取
- **Top 10 歌手**: Jony J, MC Hotdog, Tizzy T, nineone, 小鬼...

## 功能说明

### 分析引擎

- **RhymeAnalyzer**: 检测单押、双押、三押及换韵模式
- **FlowAnalyzer**: 分析音节分布、节奏密度、识别Flow风格
- **TonalAnalyzer**: 评估声调搭配、平仄交替
- **LLMAnalyzer**: 基于技术数据生成专业乐评解读（支持 mock/gpt-4/claude-3-opus/deepseek-chat）

### CLI 命令详解

| 命令 | 说明 | 示例 |
|------|------|------|
| `crawl` | 从网络抓取歌词并入库 | `python cli.py crawl --artist "Jony J" --song "奴隶"` |
| `import` | 从本地文件导入歌词 | `python cli.py import --artist "X" --song "Y" --file song.txt` |
| `search` | 查询数据库中的歌手歌曲 | `python cli.py search --artist "Jony J"` |
| `corpus` | 导出歌手全量歌词为文本 | `python cli.py corpus --artist "Jony J"` |
| `analyze` | 分析单首歌并生成解说 | `python cli.py analyze --artist "Jony J" --song "奴隶"` |
| `profile` | 生成歌手风格档案 | `python cli.py profile --artist "Jony J"` |

## 常见问题

**Q: 为什么搜索命令显示乱码？**
A: Windows终端默认GBK编码，脚本已内置UTF-8输出修复。如果仍有问题，可在命令行运行：
```cmd
chcp 65001
```

**Q: 如何添加更多歌手？**
A: 使用 `python cli.py crawl --artist "歌手名" --song "歌名"` 抓取，或手动导入歌词文件。

**Q: 如何使用真实LLM模型？**
A: 设置API Key后使用 `--model` 参数：
```bash
export OPENAI_API_KEY="your-key"
python cli.py analyze --artist "Jony J" --song "奴隶" --model gpt-4
```

**Q: HTML报告打不开或显示异常？**
A: 确保使用现代浏览器（Chrome/Edge/Firefox），报告使用纯CSS无需JavaScript。

## 测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_database.py -v
```

当前测试覆盖：歌词清洗、数据库操作、LrcCX源、手动导入源、搜索兜底源。共35个测试用例，全部通过。
