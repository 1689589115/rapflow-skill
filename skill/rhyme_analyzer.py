"""
Core Rhyme Analysis Algorithm - v1.1.0 (with multi-rhyme detection)
"""

from typing import Dict, List, Optional, Tuple
from collections import Counter
from .schemas import LineResult, RhymeUnit, MultiRhymeInfo, MultiRhymeStats


# Chinese final rhyme mapping table
FINAL_MAP: Dict[str, str] = {
    # a rhyme
    '啊': 'a', '阿': 'a',
    # ai rhyme
    '爱': 'ai', '白': 'ai', '开': 'ai', '来': 'ai', '才': 'ai',
    '海': 'ai', '改': 'ai', '快': 'ai', '买': 'ai', '外': 'ai',
    '派': 'ai', '晒': 'ai', '帅': 'ai', '台': 'ai', '歪': 'ai',
    # an rhyme
    '安': 'an', '班': 'an', '边': 'an', '办': 'an', '半': 'an',
    '但': 'an', '般': 'an', '翻': 'an', '管': 'an', '汉': 'an',
    '还': 'an', '欢': 'an', '换': 'an', '见': 'an',
    # ang rhyme
    '昂': 'ang', '棒': 'ang', '唱': 'ang', '长': 'ang', '厂': 'ang',
    '场': 'ang', '方': 'ang', '帮': 'ang', '刚': 'ang', '光': 'ang',
    '好': 'ang', '航': 'ang', '皇': 'ang', '黄': 'ang', '江': 'ang',
    '讲': 'ang', '狂': 'ang', '浪': 'ang', '亮': 'ang', '忙': 'ang',
    '强': 'ang', '让': 'ang', '上': 'ang', '爽': 'ang', '唐': 'ang',
    '旺': 'ang', '想': 'ang', '乡': 'ang', '响': 'ang', '样': 'ang',
    '张': 'ang', '掌': 'ang',
    # ao rhyme
    '奥': 'ao', '包': 'ao', '报': 'ao', '爆': 'ao', '豹': 'ao',
    '潮': 'ao', '到': 'ao', '掉': 'ao', '道': 'ao', '高': 'ao',
    '好': 'ao', '浩': 'ao', '号': 'ao', '跑': 'ao', '绕': 'ao',
    '少': 'ao', '烧': 'ao', '跳': 'ao', '笑': 'ao', '腰': 'ao',
    '早': 'ao', '造': 'ao', '照': 'ao', '找': 'ao', '走': 'ao',
    # e rhyme
    '额': 'e', '哥': 'e', '河': 'e', '和': 'e', '火': 'e',
    '过': 'e', '客': 'e', '乐': 'e', '说': 'e', '天': 'e',
    '写': 'e', '学': 'e', '这': 'e',
    # ei rhyme
    '倍': 'ei', '杯': 'ei', '被': 'ei', '飞': 'ei', '给': 'ei',
    '黑': 'ei', '回': 'ei', '灰': 'ei', '嘴': 'ei', '追': 'ei',
    # en rhyme
    '本': 'en', '奔': 'en', '比': 'en', '份': 'en', '根': 'en',
    '肯': 'en', '门': 'en', '人': 'en', '神': 'en', '身': 'en',
    '心': 'en', '音': 'en', '真': 'en', '针': 'en',
    # eng rhyme
    '更': 'eng', '风': 'eng', '疯': 'eng', '红': 'eng', '空': 'eng',
    '冷': 'eng', '梦': 'eng', '名': 'eng', '平': 'eng', '轻': 'eng',
    '情': 'eng', '晴': 'eng', '胜': 'eng', '声': 'eng', '生': 'eng',
    '痛': 'eng', '头': 'eng', '王': 'eng', '星': 'eng', '影': 'eng',
    '赢': 'eng', '应': 'eng', '硬': 'eng', '正': 'eng', '争': 'eng',
    # i rhyme
    '一': 'i', '已': 'i', '你': 'i', '起': 'i', '去': 'i',
    '是': 'i', '此': 'i', '地': 'i', '第': 'i', '理': 'i',
    '里': 'i', '题': 'i', '其': 'i', '七': 'i', '骑': 'i',
    '齐': 'i', '气': 'i',
    # ia rhyme
    '啊': 'ia', '家': 'ia', '卡': 'ia', '马': 'ia', '妈': 'ia',
    '拿': 'ia', '怕': 'ia', '沙': 'ia', '傻': 'ia', '他': 'ia',
    '瓦': 'ia', '下': 'ia', '呀': 'ia', '扎': 'ia', '抓': 'ia',
    # ian rhyme
    '安': 'ian', '班': 'ian', '边': 'ian', '办': 'ian', '半': 'ian',
    '点': 'ian', '见': 'ian', '钱': 'ian', '前': 'ian', '天': 'ian',
    '县': 'ian', '线': 'ian', '眼': 'ian', '言': 'ian', '原': 'ian',
    # iang rhyme
    '将': 'iang', '强': 'iang', '想': 'iang', '样': 'iang', '向': 'iang',
    '阳': 'iang', '杨': 'iang', '养': 'iang', '摇': 'iang', '药': 'iang',
    # iao rhyme
    '叫': 'iao', '跳': 'iao', '笑': 'iao', '小': 'iao', '要': 'iao',
    '早': 'iao', '造': 'iao', '照': 'iao', '找': 'iao', '走': 'iao',
    # ie rhyme
    '别': 'ie', '说': 'ie', '特': 'ie', '这': 'ie', '字': 'ie',
    # in rhyme
    '本': 'in', '比': 'in', '分': 'in', '门': 'in', '人': 'in',
    '神': 'in', '身': 'in', '心': 'in', '真': 'in', '针': 'in',
    # ing rhyme
    '更': 'ing', '风': 'ing', '疯': 'ing', '红': 'ing', '空': 'ing',
    '冷': 'ing', '梦': 'ing', '名': 'ing', '平': 'ing', '轻': 'ing',
    '情': 'ing', '晴': 'ing', '胜': 'ing', '声': 'ing', '生': 'ing',
    # iong rhyme
    '用': 'iong', '中': 'iong', '动': 'iong', '风': 'iong',
    '红': 'iong', '空': 'iong', '龙': 'iong', '梦': 'iong',
    '雄': 'iong', '永': 'iong', '勇': 'iong', '拥': 'iong',
    # ou rhyme
    '后': 'ou', '头': 'ou', '手': 'ou', '走': 'ou', '口': 'ou',
    '流': 'ou', '友': 'ou', '候': 'ou',
    # uan rhyme
    '安': 'uan', '办': 'uan', '半': 'uan', '关': 'uan', '看': 'uan',
    '难': 'uan', '团': 'uan', '完': 'uan', '碗': 'uan', '湾': 'uan',
    # uang rhyme
    '黄': 'uang', '光': 'uang', '狂': 'uang', '窗': 'uang', '双': 'uang',
    # ue rhyme
    '决': 'ue', '月': 'ue', '雪': 'ue', '约': 'ue', '绝': 'ue',
    # un rhyme
    '本': 'un', '门': 'un', '人': 'un', '神': 'un', '身': 'un',
    '心': 'un', '真': 'un', '针': 'un', '春': 'un', '纯': 'un',
    # uo rhyme
    '我': 'uo', '说': 'uo', '过': 'uo', '火': 'uo',
}


class RhymeAnalyzer:
    """Chinese Rap Rhyme Analyzer - v1.1.0 (with multi-rhyme detection)"""
    
    def __init__(self, mode: str = "auto", max_level: int = 4):
        self.mode = mode
        self.max_level = max_level
        self.final_map = FINAL_MAP
    
    def get_char_final(self, char: str) -> Optional[str]:
        """Get the final of a single Chinese character"""
        if char in self.final_map:
            return self.final_map[char]
        return None
    
    def extract_line_rhymes(self, line: str) -> List[Tuple[str, str, int]]:
        """Extract rhyme information from a line (with position info)"""
        rhymes = []
        chars = list(line)
        
        for i, char in enumerate(chars):
            if '\u4e00' <= char <= '\u9fa5':
                final = self.get_char_final(char)
                if final:
                    rhymes.append((char, final, i))
        
        return rhymes
    
    def analyze_multi_rhyme(self, rhymes: List[Tuple[str, str, int]]) -> Dict:
        """
        Analyze multi-rhyme structure
        
        Returns:
            dict with type, count, combinations, examples
        """
        if not rhymes:
            return {"type": "No rhyme", "count": 0, "combinations": [], "examples": []}
        
        # Count each rhyme
        rhyme_counter = Counter([final for _, final, _ in rhymes])
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
        combinations = [{rhyme: count} for rhyme, count in sorted_rhymes[:5]]
        
        # Extract ALL examples - show every rhyme occurrence without limit
        examples = []
        seen_combos = set()
        for char, final, pos in rhymes:
            combo_key = f"{char}({final})"
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
        """Calculate rhyme level"""
        if not rhymes:
            return 0
        
        rhyme_counter = Counter(rhymes)
        base_level = min(len(rhyme_counter), 3)
        
        context_match = sum(1 for r in rhymes if r in context_finals)
        match_bonus = min(context_match // 2, 2)
        
        high_freq_bonus = sum(1 for count in rhyme_counter.values() if count >= 3)
        
        total_level = base_level + match_bonus + high_freq_bonus
        return max(1, min(total_level, self.max_level))
    
    def analyse_lyric(self, lines: List[str], mark_breath: bool = True, detect_multi_rhyme: bool = True) -> Tuple:
        """Analyze a complete lyric (enhanced version)"""
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
                chinese_count = sum(1 for c in line if '\u4e00' <= c <= '\u9fa5')
                density = len(rhyme_list) / max(chinese_count, 1)
                
                rhyme_unit = RhymeUnit(
                    rhymes=rhyme_list,
                    level=level,
                    density=round(density, 3)
                )
                
                # Multi-rhyme analysis
                if detect_multi_rhyme and len(rhyme_list) >= 2:
                    multi_analysis = self.analyze_multi_rhyme(rhymes)
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
        """Add breath marks"""
        chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fa5')
        
        if chinese_count <= 8:
            return text
        
        result = []
        count = 0
        for char in text:
            result.append(char)
            if '\u4e00' <= char <= '\u9fa5':
                count += 1
                if count == 8:
                    result.append(' / ')
                    count = 0
        
        return ''.join(result)
    
    def _generate_summary(self, lines, results, avg_density, multi_rhyme_counts):
        """Generate analysis summary"""
        rhyme_lines = sum(1 for r in results if r.rhyme and r.rhyme.level > 0)
        total_lines = len(lines)
        
        summary = f"共{total_lines}行，{rhyme_lines}行有押韵，平均押韵密度{avg_density:.3f}"
        
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
