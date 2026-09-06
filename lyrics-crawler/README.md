# 中文说唱歌词爬虫引擎

一个用于抓取、清洗、存储中文说唱歌词的工具，后续可集成到 RapFlow 项目中使用。

## 功能

- **多源抓取**：从 LrcCX、Genius、网易云、Musicazi、Google搜索兜底等多个来源并发抓取
- **智能选择**：根据置信度自动选择最佳结果
- **歌词清洗**：去除 LRC 时间戳、广告语、平台水印、多余空行
- **段落拆分**：自动识别 [Verse]、[Hook]、[Chorus] 等段标
- **本地语料库**：使用 SQLite 存储，支持按歌手批量查询和导出
- **三路分析**：韵脚分析 / Flow分析 / 声调分析
- **LLM解说**：基于技术分析生成专业乐评（支持 mock/GPT/Claude/DeepSeek）
- **风格档案**：生成歌手风格画像（押韵风格、Flow特征、综合评分）
- **HTML报告**：一键生成可视化分析报告

## 数据库规模

- **歌曲数**: 2,607首
- **歌手数**: 76位
- **主要来源**: GitHub 数据集 + lrc_cx 实时抓取

## 安装

```bash
pip install -r requirements.txt
```

## 使用

### 命令行

```bash
# 搜索歌手作品
python cli.py search --artist "Jony J"

# 抓取歌词
python cli.py crawl --artist "Jony J" --song "奴隶"

# 导出语料
python cli.py corpus --artist "Jony J"

# 分析歌词
python cli.py analyze --artist "Jony J" --song "奴隶" --source github_dataset

# 生成风格档案
python cli.py profile --artist "Jony J"

# 导入本地歌词文件
python cli.py import --artist "Test Artist" --song "Test Song" --file lyrics.txt
```

### HTML 报告

```bash
# 生成可视化分析报告
python scripts/generate_report.py --artist "Jony J" --song "奴隶"
# 在浏览器中打开 reports/Jony J_奴隶_report.html
```

### 完整管道

```bash
python scripts/full_pipeline.py --artist "Jony J" --song "奴隶"
```

## 架构

```
                    ┌─────────────────┐
                    │   CLI (cli.py)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  LyricsExtractor │  ← 并发协调多个源
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌────────────┐ ┌────────────┐ ┌────────────┐
       │   LrcCX    │ │ Google搜索  │ │  手动导入   │
       │  Source    │ │  Fallback  │ │  Source    │
       └─────┬──────┘ └─────┬──────┘ └────────────┘
             │              │
             └──────┬───────┘
                    ▼
          ┌─────────────────┐
          │  Cleaner        │  ← 去时间戳、去广告、去空行
          └────────┬────────┘
                   │
          ┌────────▼────────┐
          │   SQLite DB     │  ← lyrics 表，按 (artist,song,source) 去重
          └────────┬────────┘
                   │
          ┌────────▼────────┐
          │  Analysis       │  ← 三路分析 (Rhyme/Flow/Tonal)
          │  Adapter        │
          └────────┬────────┘
                   │
          ┌────────▼────────┐
          │   LLM Analyzer  │  ← 专业乐评解说
          └────────┬────────┘
                   │
          ┌────────▼────────┐
          │  Profile Builder│  ← 风格档案生成
          └────────┬────────┘
                   │
          ┌────────▼────────┐
          │  HTML Report    │  ← 可视化分析报告
          └─────────────────┘
```

## 注意事项

- **代理设置**：所有 HTTP 请求默认走代理 `http://127.0.0.1:7897`（Clash V 默认端口）
- **编码问题**：脚本已内置 UTF-8 输出修复，Windows 终端可正常显示中文
- **LLM API**：使用真实 LLM 模型需要配置相应的 API Key（OpenAI/Anthropic/DeepSeek）
- **数据库路径**：默认使用 `data/lyrics_corpus.db`
- **反爬**：各源均有基础的反爬措施（UA 轮换、Referer 等），但仍建议控制请求频率

## 测试

```bash
python -m pytest tests/ -v
```

共 35 个测试用例，覆盖歌词清洗、数据库操作、各歌词源适配器等核心模块。
