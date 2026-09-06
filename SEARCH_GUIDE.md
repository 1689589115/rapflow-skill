# RapFlow 歌词搜索说明

## Web 应用

启动后访问 **http://localhost:8501**

## 歌词搜索（Tab 2：实时搜索）

直接输入歌手名和歌名，点击 Search 即可。
后端使用 **网易云音乐 + 酷狗音乐** 双源在线搜索。

### 数据来源
- **网易云音乐**：通过加密 API 搜索并拉取歌词（置信度 95%）
- **酷狗音乐**：通过公开 API 搜索并拉取歌词（置信度 90%）

### 注意事项
- 需要网络连接
- 歌手名/歌名尽量准确，支持模糊匹配

## 命令行用法

`ash
cd lyrics-crawler
python cli.py search --artist Jony J
python cli.py analyze --artist Jony J --song 奴隶
`

## 技术栈
- Python 3.10+
- Streamlit Web UI (port 8501)
- SQLite 本地数据库
