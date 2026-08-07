"""
歌词文本清洗与格式化工具 - v1.5.0
提供清理、分割、格式化、呼吸标记等功能
"""

import re
import sys
from typing import List


def _safe_print(*args, **kwargs):
    """跨平台安全打印，避免 Windows GBK 编码崩溃"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = " ".join(str(a) for a in args)
        text = text.encode(
            sys.stdout.encoding or "utf-8", errors="replace"
        ).decode(sys.stdout.encoding or "utf-8")
        print(text, **kwargs)


def clean_lyric(text: str) -> str:
    """
    清洗歌词文本
    - 去除括号及其内容（包括中文括号、英文括号）
    - 去除特殊符号（保留换行符）
    - 去除多余空白

    Args:
        text: 原始歌词文本

    Returns:
        清洗后的文本
    """
    # 去除括号及内容（支持中文和英文括号）
    text = re.sub(r'[（(].*?[）)]', '', text)
    text = re.sub(r'[【\[].*?[】\]]', '', text)

    # 去除特殊符号，保留汉字、字母、数字和换行
    text = re.sub(r'[^一-龥a-zA-Z0-9\n]', ' ', text)

    # 压缩多余空白
    text = re.sub(r'[ \t]+', ' ', text)

    # 去除行首行尾空白
    text = text.strip()

    return text


def split_lines(text: str) -> List[str]:
    """
    分割多行歌词
    支持换行符、回车、制表符等多种分隔符

    Args:
        text: 歌词文本

    Returns:
        行列表
    """
    # 按换行符分割
    lines = re.split(r'[\n\r\t]+', text)

    # 过滤空行
    lines = [line.strip() for line in lines if line.strip()]

    return lines


def extract_chinese_chars(text: str) -> str:
    """提取文本中的汉字"""
    return ''.join(re.findall(r'[一-龥]', text))


def calculate_chinese_count(text: str) -> int:
    """计算文本中的汉字数量"""
    return len(extract_chinese_chars(text))


def insert_breath_mark(text: str, interval: int = 8) -> str:
    """
    在文本中插入换气标记
    每 interval 个汉字插入一个 " / "

    Args:
        text: 原始文本
        interval: 汉字间隔，默认8

    Returns:
        带换气标记的文本
    """
    chinese_chars = extract_chinese_chars(text)

    if len(chinese_chars) <= interval:
        return text

    # 构建带标记的文本
    result = []
    char_count = 0

    for char in text:
        result.append(char)
        if '一' <= char <= '龥':
            char_count += 1
            if char_count > 0 and char_count % interval == 0:
                # 检查下一个字符是否已经是换行或标记
                if result and result[-1] not in ['/ ', '\n', '\r']:
                    result.append(' / ')

    return ''.join(result)
