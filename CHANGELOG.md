# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.5.0] - 2026-08-07

### Fixed
- **Pydantic v2 弃用警告**: 将 `class Config` 替换为 `model_config = ConfigDict(...)`，消除 2 条 `PydanticDeprecatedSince20` 警告
- **Windows GBK 编码崩溃**: 新增 `_safe_print()` 工具函数，捕获 `UnicodeEncodeError` 并替换无法编码的字符；三个 demo 文件移除 emoji 避免崩溃
- **呼吸标记逻辑重复**: `rhyme_analyzer._add_breath_mark()` 委托给 `utils.insert_breath_mark()`，消除重复实现
- **Unicode 编码可读性**: 将 `'一'`/`'龥'` 替换为直接汉字 `'一'`/`'龥'`
- **重复导入**: 移除 `core.py` 中的 `_safe_print` 和 `sys` 导入，统一使用 `utils` 中的版本
- **Flow 评分逻辑**: 重构为互斥的正交评分，避免各风格区间重叠导致的误判
- **依赖清理**: 移除未使用的 `jieba` 依赖

### Added
- **Flow 节奏分析**: 新增 `skill/flow_analyzer.py`，支持识别 Boom Bap / Trap / Drill / Chopper / Melodic 五种风格
- **`analyze_flow` 参数**: `RapFlowInput` 新增 `analyze_flow` 布尔参数，默认开启
- **`FlowInfo` Schema**: 新增 Flow 分析结果 Pydantic 模型
- **`_safe_print` 工具**: `utils.py` 新增跨平台安全打印函数
- **新增测试**: `test_flow_boom_bap`、`test_flow_trap`、`test_flow_analysis_chopper` 等
- **pytest-cov**: 添加 Coverage 支持
- **Python 3.13**: `pyproject.toml` 添加 Python 3.13 分类器

### Changed
- `pyproject.toml`: 版本 `1.4.0` → `1.5.0`，移除 `jieba` 依赖
- `.github/workflows/test.yml`: 移除 Python 3.9，保留 3.10/3.11/3.12
- `requirements.txt`: 移除 `jieba>=0.42.1`
- `.gitignore`: 补全 `build/`、`dist/`、`release_*`、`*.pyc`、`venv/` 等忽略规则
- 所有源码文件头部注释版本统一为 `v1.5.0`

### Removed
- `jieba` 依赖（不再使用）
- `core.py` 中的重复 `_safe_print` 定义

## [v1.4.0] - 2026-08-05

### Added
- Flow 节奏分析（初版）

## [v1.3.0] - 2026-08-04

### Added
- 韵母归一化系统

## [v1.2.0] - 2026-08-04

### Added
- 韵母数据库扩展至 20,992 个汉字

## [v1.1.0] - 2026-08-04

### Added
- 多押检测功能
