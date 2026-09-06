# RapFlow — 中文说唱歌词创作与歌词搜索平台

> AI 驱动的中文说唱歌词生成 · 网易云/酷狗歌词搜索 · 三路分析引擎

## 功能

| 功能 | 说明 |
|------|------|
| 歌词创作 | 基于 Agnes AI 的 LLM，模仿指定歌手风格生成原创歌词 |
| 歌词搜索 | 联网搜索网易云 + 酷狗歌词，实时获取原曲歌词 |
| 三路分析 | 押韵密度 · Flow 风格识别 · 声调搭配评估 |
| AI 乐评 | 基于技术分析结果生成专业乐评 |

## Web 应用

启动后访问 http://localhost:8501

`ash
# 安装依赖
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env

# 启动
python -m streamlit run app.py --server.port 8501 --server.headless true
`

或直接双击 start.bat。

## 项目结构

`
rap/
  ├── app.py                    # Streamlit Web UI
  ├── requirements.txt          # Python 依赖
  ├── .env                      # API Key（不提交到 git）
  ├── lyrics-crawler/           # 歌词爬虫 + 数据库
  │   ├── crawler/sources/
  │   │   └── music_dl_source.py  # 网易云 + 酷狗搜索
  │   └── data/
  │       └── lyrics_corpus.db  # SQLite 语料库
  ├── clean-rapflow-skill/      # 三路分析引擎
  │   └── skill/
  │       ├── rhyme_analyzer.py
  │       ├── flow_analyzer.py
  │       └── tonal_analyzer.py
  └── mcp_server.py            # MCP 协议服务器
`

## 技术栈

- **Web UI**: Streamlit
- **LLM**: Agnes AI (agnes-2.5-flash)
- **歌词源**: 网易云音乐 API、酷狗音乐 API
- **分析引擎**: pypinyin + 自定义算法
- **数据库**: SQLite

## 命令行用法

`ash
cd lyrics-crawler
python cli.py search --artist Jony J
python cli.py analyze --artist Jony J --song 奴隶
`

## 测试

`ash
cd lyrics-crawler
python -m pytest tests/ -v
`

## License

MIT
