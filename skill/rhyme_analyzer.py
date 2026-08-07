"""
Core Rhyme Analysis Algorithm - v1.5.0 (Rhyme Normalization + Flow Analysis)
基于pypinyin自动生成 + 韵母归一化 + Flow节奏分析
"""

from typing import Dict, List, Optional, Tuple
from collections import Counter
from .schemas import LineResult, RhymeUnit, MultiRhymeInfo, MultiRhymeStats
from .utils import insert_breath_mark


# ============================================
# 韵母归一化映射表 - v1.3.0
# 将相似韵母合并，减少误判
# ============================================

# 归一化规则：将相似韵母映射到标准韵母
NORMALIZATION_MAP = {
    # 鼻韵母归一化（关键）
    'ing': 'in',      # ing → in
    'iong': 'in',     # iong → in
    'iang': 'ian',    # iang → ian
    'uang': 'uan',    # uang → uan
    'eng': 'en',      # eng → en
    'ong': 'en',      # ong → en (方言/口语中常混用)
    
    # 元音归一化
    'iou': 'ou',      # iou → ou
    'uei': 'ui',      # uei → ui
    'uen': 'un',      # uen → un
    
    # 保持不变的常用韵母
    'a': 'a',
    'ai': 'ai',
    'an': 'an',
    'ao': 'ao',
    'e': 'e',
    'ei': 'ei',
    'en': 'en',
    'er': 'er',
    'i': 'i',
    'ia': 'ia',
    'ian': 'ian',
    'iao': 'iao',
    'ie': 'ie',
    'in': 'in',
    'iu': 'iu',
    'n': 'n',        # 特殊鼻音
    'o': 'o',
    'ou': 'ou',
    'u': 'u',
    'ua': 'ua',
    'uai': 'uai',
    'uan': 'uan',
    'ue': 'ue',
    'ui': 'ui',
    'un': 'un',
    'uo': 'uo',
    'v': 'v',        #  ü
}


class RhymeNormalizer:
    """韵母归一化器"""
    
    @staticmethod
    def normalize(final: str) -> str:
        """将韵母归一化到标准形式"""
        if not final:
            return final
        return NORMALIZATION_MAP.get(final, final)
    
    @staticmethod
    def normalize_list(rhymes: List[str]) -> List[str]:
        """批量归一化韵母列表"""
        return [RhymeNormalizer.normalize(f) for f in rhymes]
    
    @staticmethod
    def get_normalized_stats(rhymes: List[str]) -> Dict:
        """获取归一化后的统计信息"""
        normalized = RhymeNormalizer.normalize_list(rhymes)
        counter = Counter(normalized)
        return {
            'normalized': normalized,
            'unique_count': len(counter),
            'distribution': dict(counter.most_common())
        }


def _load_extended_rhyme_map():
    """加载扩展版韵母映射（使用pypinyin动态生成）"""
    try:
        from pypinyin import pinyin, Style
        rhyme_map = {}
        for i in range(0x4E00, 0x9FFF + 1):
            char = chr(i)
            try:
                py_result = pinyin(char, style=Style.FINALS)
                if py_result and len(py_result[0]) > 0:
                    final = py_result[0][0]
                    rhyme_map[char] = final
            except:
                pass
        return rhyme_map
    except ImportError:
        # fallback to basic map
        return _get_basic_rhyme_map()


def _get_basic_rhyme_map():
    """基础韵母映射（当pypinyin不可用时使用）"""
    return {
        # i韵高频字
        '一': 'i', '已': 'i', '你': 'i', '起': 'i', '去': 'i',
        '是': 'i', '此': 'i', '地': 'i', '第': 'i', '理': 'i',
        '里': 'i', '题': 'i', '其': 'i', '七': 'i', '骑': 'i',
        '齐': 'i', '气': 'i', '意': 'i', '艺': 'i', '易': 'i',
        # e韵高频字
        '额': 'e', '哥': 'e', '河': 'e', '和': 'e', '火': 'e',
        '过': 'e', '客': 'e', '乐': 'e', '说': 'e', '天': 'e',
        '写': 'e', '学': 'e', '这': 'e',
        # uo韵高频字
        '我': 'uo', '说': 'uo', '过': 'uo', '火': 'uo', '活': 'uo',
        # u韵高频字
        '不': 'u', '去': 'u', '路': 'u', '舞': 'u', '苦': 'u',
        # an韵高频字
        '安': 'an', '班': 'an', '边': 'an', '办': 'an', '半': 'an',
        '但': 'an', '般': 'an', '翻': 'an', '管': 'an', '汉': 'an',
        # ang韵高频字
        '昂': 'ang', '棒': 'ang', '唱': 'ang', '长': 'ang', '厂': 'ang',
        '场': 'ang', '方': 'ang', '帮': 'ang', '刚': 'ang', '光': 'ang',
        '好': 'ang', '航': 'ang', '皇': 'ang', '黄': 'ang', '江': 'ang',
        # ao韵高频字
        '奥': 'ao', '包': 'ao', '报': 'ao', '爆': 'ao', '豹': 'ao',
        '潮': 'ao', '到': 'ao', '掉': 'ao', '道': 'ao', '高': 'ao',
        # eng韵高频字
        '更': 'eng', '风': 'eng', '疯': 'eng', '红': 'eng', '空': 'eng',
        '冷': 'eng', '梦': 'eng', '名': 'eng', '平': 'eng', '轻': 'eng',
        # in韵高频字
        '本': 'in', '比': 'in', '分': 'in', '门': 'in', '人': 'in',
        '神': 'in', '身': 'in', '心': 'in', '真': 'in', '针': 'in',
        # ing韵高频字
        '更': 'ing', '风': 'ing', '疯': 'ing', '红': 'ing', '空': 'ing',
        '冷': 'ing', '梦': 'ing', '名': 'ing', '平': 'ing', '轻': 'ing',
        # iong韵高频字
        '用': 'iong', '中': 'iong', '动': 'iong', '龙': 'iong',
        '雄': 'iong', '永': 'iong', '勇': 'iong', '拥': 'iong',
        # ou韵高频字
        '后': 'ou', '头': 'ou', '手': 'ou', '走': 'ou', '口': 'ou',
        # ue韵高频字
        '决': 'ue', '月': 'ue', '雪': 'ue', '约': 'ue', '绝': 'ue',
        # ian韵高频字
        '安': 'ian', '班': 'ian', '边': 'ian', '见': 'ian', '钱': 'ian',
        # iang韵高频字
        '将': 'iang', '强': 'iang', '想': 'iang', '样': 'iang', '向': 'iang',
        # iao韵高频字
        '叫': 'iao', '跳': 'iao', '笑': 'iao', '小': 'iao', '要': 'iao',
        # ie韵高频字
        '别': 'ie', '说': 'ie', '这': 'ie', '字': 'ie',
        # uan韵高频字
        '安': 'uan', '办': 'uan', '关': 'uan', '看': 'uan', '难': 'uan',
        # uang韵高频字
        '黄': 'uang', '光': 'uang', '狂': 'uang', '窗': 'uang', '双': 'uang',
    }


# 加载扩展映射
FINAL_MAP = _load_extended_rhyme_map()


class RhymeAnalyzer:
    """Chinese Rap Rhyme Analyzer - v1.5.0 (with Rhyme Normalization & Flow Analysis)"""
    
    def __init__(self, mode: str = "auto", max_level: int = 4, 
                 normalize: bool = True):
        self.mode = mode
        self.max_level = max_level
        self.final_map = FINAL_MAP
        self.normalize = normalize  # 是否启用归一化
    
    def get_char_final(self, char: str) -> Optional[str]:
        """Get the final of a single Chinese character"""
        if char in self.final_map:
            final = self.final_map[char]
            # 应用归一化
            if self.normalize:
                return RhymeNormalizer.normalize(final)
            return final
        return None
    
    def extract_line_rhymes(self, line: str) -> List[Tuple[str, str, int]]:
        """Extract rhyme information from a line (with position info)"""
        rhymes = []
        chars = list(line)
        
        for i, char in enumerate(chars):
            if '一' <= char <= '龥':
                final = self.get_char_final(char)
                if final:
                    rhymes.append((char, final, i))
        
        return rhymes
    
    def analyze_multi_rhyme(self, rhymes: List[Tuple[str, str, int]], 
                           use_normalized: bool = True) -> Dict:
        """
        Analyze multi-rhyme structure
        
        Args:
            rhymes: List of (char, final, position) tuples
            use_normalized: Whether to use normalized rhymes for analysis
            
        Returns:
            dict with type, count, combinations, examples
        """
        if not rhymes:
            return {"type": "No rhyme", "count": 0, "combinations": [], "examples": []}
        
        # 选择使用原始还是归一化韵母
        if use_normalized and self.normalize:
            rhyme_list = [RhymeNormalizer.normalize(final) for _, final, _ in rhymes]
        else:
            rhyme_list = [final for _, final, _ in rhymes]
        
        # Count each rhyme
        rhyme_counter = Counter(rhyme_list)
        sorted_rhymes = rhyme_counter.most_common()
        
        unique_count = len(sorted_rhymes)
        
        # Determine multi-rhyme type
        if unique_count == 1:
            rhyme_type = "单押"
        elif unique_count == 2:
            rhyme_type = "双押"
        elif unique_count == 3:
            rhyme_type = "三押"
        elif unique_count == 4:
            rhyme_type = "四押"
        else:
            rhyme_type = f"{unique_count}押"
        
        # Build combination info
        combinations = [{rhyme: count} for rhyme, count in sorted_rhymes[:10]]
        
        # Extract ALL examples - show every rhyme occurrence without limit
        examples = []
        seen_combos = set()
        for char, final, pos in rhymes:
            # 显示时展示归一化后的韵母，但保留原始汉字
            norm_final = RhymeNormalizer.normalize(final) if self.normalize else final
            combo_key = f"{char}({norm_final})"
            if combo_key not in seen_combos:
                examples.append(combo_key)
                seen_combos.add(combo_key)
        
        return {
            "type": rhyme_type,
            "count": unique_count,
            "combinations": combinations,
            "examples": examples
        }
    
    def calc_rhyme_level(self, rhymes: List[str], context_finals: List[str]) -> int:
        """Calculate rhyme level (with normalization support)"""
        if not rhymes:
            return 0
        
        # 应用归一化
        if self.normalize:
            norm_rhymes = RhymeNormalizer.normalize_list(rhymes)
            norm_context = RhymeNormalizer.normalize_list(context_finals)
        else:
            norm_rhymes = rhymes
            norm_context = context_finals
        
        rhyme_counter = Counter(norm_rhymes)
        base_level = min(len(rhyme_counter), 3)
        
        context_match = sum(1 for r in norm_rhymes if r in norm_context)
        match_bonus = min(context_match // 2, 2)
        
        high_freq_bonus = sum(1 for count in rhyme_counter.values() if count >= 3)
        
        total_level = base_level + match_bonus + high_freq_bonus
        return max(1, min(total_level, self.max_level))
    
    def analyse_lyric(self, lines: List[str], mark_breath: bool = True, 
                     detect_multi_rhyme: bool = True) -> Tuple:
        """Analyze a complete lyric (enhanced version with normalization)"""
        if not lines:
            return [], 0.0, "Empty lyrics", None
        
        results = []
        total_density = 0.0
        context_finals = []
        
        # Multi-rhyme statistics
        multi_rhyme_counts = Counter()
        multi_rhyme_examples = []
        
        for idx, line in enumerate(lines):
            # Extract rhymes
            rhymes = self.extract_line_rhymes(line)
            rhyme_list = [final for _, final, _ in rhymes]
            
            # Initialize multi_rhyme before use
            multi_rhyme = None
            
            # Basic rhyme analysis
            if rhyme_list:
                level = self.calc_rhyme_level(rhyme_list, context_finals)
                chinese_count = sum(1 for c in line if '一' <= c <= '龥')
                density = len(rhyme_list) / max(chinese_count, 1)
                
                rhyme_unit = RhymeUnit(
                    rhymes=rhyme_list,
                    level=level,
                    density=round(density, 3)
                )
                
                # Multi-rhyme analysis
                if detect_multi_rhyme and len(rhyme_list) >= 2:
                    multi_analysis = self.analyze_multi_rhyme(rhymes, use_normalized=True)
                    multi_rhyme = MultiRhymeInfo(
                        type=multi_analysis["type"],
                        count=multi_analysis["count"],
                        rhyme_combinations=multi_analysis["combinations"],
                        examples=multi_analysis["examples"]
                    )
                    
                    # Record multi-rhyme statistics
                    multi_rhyme_counts[multi_analysis["type"]] += 1
                    multi_rhyme_examples.append({
                        "line": line[:50] + "..." if len(line) > 50 else line,
                        "type": multi_analysis["type"],
                        "rhymes": rhyme_list,
                        "examples": multi_analysis["examples"]
                    })
                
                context_finals.extend(rhyme_list)
            else:
                rhyme_unit = RhymeUnit(rhymes=[], level=0, density=0.0)
            
            # Generate breath marks
            breath_mark = None
            if mark_breath:
                breath_mark = self._add_breath_mark(line)
            
            line_result = LineResult(
                line_index=idx,
                text=line,
                rhyme=rhyme_unit,
                multi_rhyme=multi_rhyme,
                breath_mark=breath_mark
            )
            results.append(line_result)
            total_density += rhyme_unit.density
        
        avg_density = round(total_density / len(lines), 3) if lines else 0.0
        
        # Generate multi-rhyme statistics
        multi_stats = None
        if detect_multi_rhyme:
            multi_stats = self._generate_multi_rhyme_stats(lines, multi_rhyme_counts, multi_rhyme_examples)
        
        summary = self._generate_summary(lines, results, avg_density, multi_rhyme_counts)
        
        return results, avg_density, summary, multi_stats
    
    def _generate_multi_rhyme_stats(self, lines, counts, examples):
        """Generate multi-rhyme statistics"""
        total = sum(counts.values())
        
        return MultiRhymeStats(
            total_lines=len(lines),
            single_rhyme_lines=counts.get("单押", 0),
            double_rhyme_lines=counts.get("双押", 0),
            triple_rhyme_lines=counts.get("三押", 0),
            quad_rhyme_lines=counts.get("四押", 0),
            multi_rhyme_lines=total - counts.get("单押", 0) - counts.get("双押", 0) - counts.get("三押", 0) - counts.get("四押", 0),
            most_common_pattern=counts.most_common(1)[0][0] if counts else "无押韵",
            detailed_examples=examples[:10]
        )
    
    def _add_breath_mark(self, text: str) -> str:
        """\u6dfb\u52a0\u6362\u6c14\u6807\u8bb0\uff08\u59d4\u6258\u7ed9 utils.insert_breath_mark\uff09"""
        return insert_breath_mark(text)
    
    def _generate_summary(self, lines, results, avg_density, multi_rhyme_counts):
        """Generate analysis summary"""
        rhyme_lines = sum(1 for r in results if r.rhyme and r.rhyme.level > 0)
        total_lines = len(lines)
        
        normalize_info = " (已启用韵母归一化)" if self.normalize else ""
        summary = f"共{total_lines}行，{rhyme_lines}行有押韵，平均押韵密度{avg_density:.3f}{normalize_info}"
        
        best_line = None
        best_level = 0
        for r in results:
            if r.rhyme and r.rhyme.level > best_level:
                best_level = r.rhyme.level
                best_line = r
        
        if best_line:
            summary += f"，最佳押韵在第{best_line.line_index + 1}行（等级{best_level}）"
        
        if multi_rhyme_counts:
            most_common = multi_rhyme_counts.most_common(1)[0]
            summary += f"，最常见的多押类型为{most_common[0]}（{most_common[1]}次）"
        
        return summary
