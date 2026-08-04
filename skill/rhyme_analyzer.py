"""
核心押韵分析算法
包含韵母映射、押韵检测、多押识别等功能
"""

from typing import Dict, List, Optional, Tuple
from collections import Counter


# 中文尾韵韵母映射表（基于拼音韵母）
FINAL_MAP: Dict[str, str] = {
    # a 韵
    '啊': 'a', '阿': 'a',
    # ai 韵
    '爱': 'ai', '白': 'ai', '开': 'ai', '来': 'ai', '才': 'ai',
    '海': 'ai', '改': 'ai', '快': 'ai', '买': 'ai', '外': 'ai',
    '派': 'ai', '晒': 'ai', '帅': 'ai', '台': 'ai', '歪': 'ai',
    # an 韵
    '安': 'an', '班': 'an', '边': 'an', '办': 'an', '半': 'an',
    '但': 'an', '般': 'an', '翻': 'an', '管': 'an', '汉': 'an',
    '还': 'an', '欢': 'an', '换': 'an', '见': 'an',
    # ang 韵
    '昂': 'ang', '棒': 'ang', '唱': 'ang', '长': 'ang', '厂': 'ang',
    '场': 'ang', '方': 'ang', '帮': 'ang', '刚': 'ang', '光': 'ang',
    '好': 'ang', '航': 'ang', '皇': 'ang', '黄': 'ang', '江': 'ang',
    '讲': 'ang', '狂': 'ang', '浪': 'ang', '亮': 'ang', '忙': 'ang',
    '强': 'ang', '让': 'ang', '上': 'ang', '爽': 'ang', '唐': 'ang',
    '旺': 'ang', '想': 'ang', '乡': 'ang', '响': 'ang', '样': 'ang',
    '张': 'ang', '掌': 'ang',
    # ao 韵
    '奥': 'ao', '包': 'ao', '报': 'ao', '爆': 'ao', '豹': 'ao',
    '潮': 'ao', '到': 'ao', '掉': 'ao', '道': 'ao', '高': 'ao',
    '好': 'ao', '浩': 'ao', '号': 'ao', '跑': 'ao', '绕': 'ao',
    '少': 'ao', '烧': 'ao', '跳': 'ao', '笑': 'ao', '腰': 'ao',
    '早': 'ao', '造': 'ao', '照': 'ao', '找': 'ao', '走': 'ao',
    # e 韵
    '额': 'e', '哥': 'e', '河': 'e', '和': 'e', '火': 'e',
    '过': 'e', '客': 'e', '乐': 'e', '说': 'e', '天': 'e',
    '写': 'e', '学': 'e', '这': 'e',
    # ei 韵
    '倍': 'ei', '杯': 'ei', '被': 'ei', '飞': 'ei', '给': 'ei',
    '黑': 'ei', '回': 'ei', '灰': 'ei', '嘴': 'ei', '追': 'ei',
    # en 韵
    '本': 'en', '奔': 'en', '比': 'en', '份': 'en', '根': 'en',
    '肯': 'en', '门': 'en', '人': 'en', '神': 'en', '身': 'en',
    '心': 'en', '音': 'en', '真': 'en', '针': 'en',
    # eng 韵
    '更': 'eng', '风': 'eng', '疯': 'eng', '红': 'eng', '空': 'eng',
    '冷': 'eng', '梦': 'eng', '名': 'eng', '平': 'eng', '轻': 'eng',
    '情': 'eng', '晴': 'eng', '胜': 'eng', '声': 'eng', '生': 'eng',
    '痛': 'eng', '头': 'eng', '王': 'eng', '星': 'eng', '影': 'eng',
    '赢': 'eng', '应': 'eng', '硬': 'eng', '正': 'eng', '争': 'eng',
    # i 韵
    '一': 'i', '已': 'i', '你': 'i', '起': 'i', '去': 'i',
    '是': 'i', '此': 'i', '地': 'i', '第': 'i', '理': 'i',
    '里': 'i', '题': 'i', '其': 'i', '七': 'i', '骑': 'i',
    '齐': 'i', '气': 'i',
    # ia 韵
    '啊': 'ia', '家': 'ia', '卡': 'ia', '马': 'ia', '妈': 'ia',
    '拿': 'ia', '怕': 'ia', '沙': 'ia', '傻': 'ia', '他': 'ia',
    '瓦': 'ia', '下': 'ia', '呀': 'ia', '扎': 'ia', '抓': 'ia',
    # ian 韵
    '安': 'ian', '班': 'ian', '边': 'ian', '办': 'ian', '半': 'ian',
    '点': 'ian', '见': 'ian', '钱': 'ian', '前': 'ian', '天': 'ian',
    '县': 'ian', '线': 'ian', '眼': 'ian', '言': 'ian', '原': 'ian',
    # iang 韵
    '将': 'iang', '强': 'iang', '想': 'iang', '样': 'iang', '向': 'iang',
    '阳': 'iang', '杨': 'iang', '养': 'iang', '摇': 'iang', '药': 'iang',
    # iao 韵
    '叫': 'iao', '跳': 'iao', '笑': 'iao', '小': 'iao', '要': 'iao',
    '早': 'iao', '造': 'iao', '照': 'iao', '找': 'iao', '走': 'iao',
    # ie 韵
    '别': 'ie', '说': 'ie', '特': 'ie', '这': 'ie', '字': 'ie',
    # in 韵
    '本': 'in', '比': 'in', '分': 'in', '门': 'in', '人': 'in',
    '神': 'in', '身': 'in', '心': 'in', '真': 'in', '针': 'in',
    # ing 韵
    '更': 'ing', '风': 'ing', '疯': 'ing', '红': 'ing', '空': 'ing',
    '冷': 'ing', '梦': 'ing', '名': 'ing', '平': 'ing', '轻': 'ing',
    '情': 'ing', '晴': 'ing', '胜': 'ing', '声': 'ing', '生': 'ing',
    # iong 韵
    '用': 'iong', '中': 'iong', '动': 'iong', '风': 'iong',
    '红': 'iong', '空': 'iong', '龙': 'iong', '梦': 'iong',
    '雄': 'iong', '永': 'iong', '勇': 'iong', '拥': 'iong',
    # ou 韵
    '后': 'ou', '头': 'ou', '手': 'ou', '走': 'ou', '口': 'ou',
    '流': 'ou', '友': 'ou', '候': 'ou',
    # uan 韵
    '安': 'uan', '办': 'uan', '半': 'uan', '关': 'uan', '看': 'uan',
    '难': 'uan', '团': 'uan', '完': 'uan', '碗': 'uan', '湾': 'uan',
    # uang 韵
    '黄': 'uang', '光': 'uang', '狂': 'uang', '窗': 'uang', '双': 'uang',
    # ue 韵
    '决': 'ue', '月': 'ue', '雪': 'ue', '约': 'ue', '绝': 'ue',
    # un 韵
    '本': 'un', '门': 'un', '人': 'un', '神': 'un', '身': 'un',
    '心': 'un', '真': 'un', '针': 'un', '春': 'un', '纯': 'un',
    # uo 韵
    '我': 'uo', '说': 'uo', '过': 'uo', '火': 'uo',
}


# 简单汉字韵母字典
SIMPLE_CHAR_FINAL: Dict[str, str] = {
    '啊': 'a', '爱': 'ai', '安': 'an', '昂': 'ang', '奥': 'ao',
    '吧': 'a', '白': 'ai', '班': 'an', '棒': 'ang', '包': 'ao',
    '被': 'ei', '本': 'en', '逼': 'i', '别': 'ie', '病': 'ing',
    '表': 'iao', '变': 'ian', '并': 'ing', '波': 'o', '不': 'u',
    '才': 'ai', '菜': 'ai', '参': 'an', '草': 'ao', '拆': 'ai',
    '唱': 'ang', '超': 'ao', '车': 'e', '成': 'eng', '城': 'eng',
    '吃': 'i', '出': 'u', '处': 'u', '初': 'u', '穿': 'uan',
    '窗': 'uang', '创': 'uang', '从': 'ong', '错': 'uo', '大': 'a',
    '代': 'ai', '带': 'ai', '单': 'an', '当': 'ang', '到': 'ao',
    '得': 'e', '的': 'e', '等': 'eng', '低': 'i', '地': 'i',
    '点': 'ian', '电': 'ian', '店': 'ian', '掉': 'iao', '爹': 'ie',
    '丁': 'ing', '定': 'ing', '动': 'ong', '都': 'ou', '读': 'u',
    '多': 'uo', '鹅': 'e', '恩': 'en', '儿': 'er', '发': 'a',
    '法': 'a', '翻': 'an', '房': 'ang', '飞': 'ei', '分': 'en',
    '风': 'eng', '佛': 'o', '福': 'u', '改': 'ai', '干': 'an',
    '刚': 'ang', '高': 'ao', '哥': 'e', '各': 'e', '给': 'ei',
    '根': 'en', '更': 'eng', '工': 'ong', '公': 'ong', '共': 'ong',
    '光': 'ang', '归': 'ui', '国': 'uo', '好': 'ao', '喝': 'e',
    '和': 'e', '后': 'ou', '护': 'u', '花': 'ua', '坏': 'uai',
    '还': 'an', '黄': 'uang', '灰': 'ui', '活': 'uo', '或': 'uo',
    '机': 'i', '家': 'ia', '甲': 'ia', '间': 'ian', '将': 'iang',
    '讲': 'ang', '叫': 'iao', '街': 'ie', '结': 'ie', '近': 'in',
    '惊': 'ing', '镜': 'ing', '酒': 'iou', '旧': 'iu', '君': 'un',
    '开': 'ai', '看': 'an', '康': 'ang', '考': 'ao', '可': 'e',
    '刻': 'e', '肯': 'en', '空': 'ong', '口': 'ou', '哭': 'u',
    '快': 'uai', '来': 'ai', '蓝': 'an', '廊': 'ang', '老': 'ao',
    '乐': 'e', '里': 'i', '连': 'ian', '凉': 'ang', '两': 'ang',
    '料': 'iao', '列': 'ie', '邻': 'in', '领': 'ing', '流': 'ou',
    '龙': 'ong', '楼': 'ou', '路': 'u', '乱': 'uan', '略': 'üe',
    '妈': 'a', '买': 'ai', '迈': 'ai', '满': 'an', '忙': 'ang',
    '毛': 'ao', '没': 'ei', '门': 'en', '猛': 'eng', '命': 'ing',
    '摸': 'o', '木': 'u', '拿': 'a', '南': 'an', '难': 'an',
    '脑': 'ao', '你': 'i', '牛': 'iu', '拍': 'ai', '牌': 'ai',
    '跑': 'ao', '捧': 'eng', '批': 'i', '篇': 'ian', '飘': 'iao',
    '平': 'ing', '破': 'o', '期': 'i', '骑': 'i', '钱': 'ian',
    '强': 'iang', '桥': 'iao', '切': 'ie', '青': 'ing', '情': 'ing',
    '秋': 'iu', '全': 'uan', '然': 'an', '软': 'uan', '洒': 'a',
    '赛': 'ai', '三': 'an', '桑': 'ang', '扫': 'ao', '色': 'e',
    '沙': 'a', '山': 'an', '伤': 'ang', '上': 'ang', '少': 'ao',
    '社': 'e', '深': 'en', '神': 'en', '声': 'eng', '生': 'eng',
    '胜': 'eng', '十': 'i', '时': 'i', '实': 'i', '世': 'i',
    '事': 'i', '手': 'ou', '受': 'ou', '书': 'u', '树': 'u',
    '数': 'u', '双': 'uang', '睡': 'ui', '说': 'uo', '丝': 'i',
    '送': 'ong', '岁': 'ui', '他': 'a', '太': 'ai', '谈': 'an',
    '唐': 'ang', '特': 'e', '提': 'i', '天': 'ian', '条': 'iao',
    '铁': 'ie', '停': 'ing', '同': 'ong', '头': 'ou', '图': 'u',
    '团': 'uan', '玩': 'an', '往': 'ang', '万': 'an', '王': 'ang',
    '危': 'ei', '文': 'en', '我': 'o', '西': 'i', '喜': 'i',
    '下': 'ia', '先': 'ian', '向': 'iang', '小': 'iao', '些': 'ie',
    '新': 'in', '星': 'ing', '学': 'ue', '压': 'a', '烟': 'ian',
    '扬': 'ang', '药': 'iao', '也': 'e', '叶': 'ie', '一': 'i',
    '衣': 'i', '音': 'in', '应': 'ing', '用': 'iong', '鱼': 'ü',
    '雨': 'ü', '远': 'uan', '月': 'üe', '在': 'ai', '赞': 'an',
    '脏': 'ang', '造': 'ao', '这': 'e', '真': 'en', '正': 'eng',
    '知': 'i', '中': 'ong', '种': 'ong', '重': 'ong', '州': 'ou',
    '周': 'ou', '朱': 'u', '主': 'u', '住': 'u', '抓': 'ua',
    '转': 'uan', '装': 'uang', '状': 'uang', '最': 'ui', '醉': 'ui',
    '走': 'ou', '左': 'uo', '做': 'uo', '嘴': 'ui',
}


class RhymeAnalyzer:
    """中文说唱押韵分析器"""
    
    def __init__(self, mode: str = "auto", max_level: int = 4):
        """
        初始化分析器
        
        Args:
            mode: 分析模式（auto/strict/casual）
            max_level: 最大押韵等级（1-6）
        """
        self.mode = mode
        self.max_level = max_level
        self.final_map = FINAL_MAP
        self.simple_char_final = SIMPLE_CHAR_FINAL
    
    def get_char_final(self, char: str) -> Optional[str]:
        """
        获取单个汉字的韵母
        
        Args:
            char: 汉字
            
        Returns:
            韵母字符串，如果不在映射表中则返回None
        """
        # 先查完整映射表
        if char in self.final_map:
            return self.final_map[char]
        
        # 再查简化映射表
        if char in self.simple_char_final:
            return self.simple_char_final[char]
        
        return None
    
    def extract_line_finals(self, line: str) -> List[Tuple[str, str]]:
        """
        提取行末韵母（反向扫描）
        
        Args:
            line: 歌词文本行
            
        Returns:
            韵母列表 [(汉字, 韵母)]
        """
        finals = []
        chars = list(line)
        
        # 反向扫描最后10个字符
        scan_count = min(10, len(chars))
        for i in range(len(chars) - 1, len(chars) - scan_count - 1, -1):
            char = chars[i]
            # 只处理汉字
            if '\u4e00' <= char <= '\u9fa5':
                final = self.get_char_final(char)
                if final:
                    finals.append((char, final))
        
        return finals
    
    def calc_line_rhyme(self, line: str, context_finals: List[str]) -> 'RhymeUnit':
        """
        计算单行押韵信息
        
        Args:
            line: 歌词文本
            context_finals: 上下文的韵母列表
            
        Returns:
            RhymeUnit 押韵单元
        """
        from .schemas import RhymeUnit
        
        # 提取本行韵母
        line_finals = self.extract_line_finals(line)
        
        if not line_finals:
            return RhymeUnit(rhymes=[], level=0, density=0.0)
        
        # 获取韵母列表
        rhyme_list = [final for _, final in line_finals]
        
        # 计算押韵等级
        level = self._calc_rhyme_level(rhyme_list, context_finals)
        
        # 计算押韵密度
        chinese_count = sum(1 for c in line if '\u4e00' <= c <= '\u9fa5')
        density = len(rhyme_list) / max(chinese_count, 1)
        
        return RhymeUnit(
            rhymes=rhyme_list,
            level=level,
            density=round(density, 3)
        )
    
    def _calc_rhyme_level(self, rhyme_list: List[str], context_finals: List[str]) -> int:
        """
        计算押韵等级（1-6）
        
        逻辑：
        - 如果韵母与上下文匹配，等级+1
        - 同一韵母出现次数越多，等级越高
        - 最多6级
        """
        if not rhyme_list:
            return 0
        
        # 统计韵母出现频率
        rhyme_counter = Counter(rhyme_list)
        
        # 基础等级：基于韵母数量
        base_level = min(len(rhyme_counter), 3)
        
        # 与上下文匹配的奖励
        context_match = sum(1 for r in rhyme_list if r in context_finals)
        match_bonus = min(context_match // 2, 2)
        
        # 高频韵母奖励
        high_freq_bonus = 0
        for rhyme, count in rhyme_counter.items():
            if count >= 3:
                high_freq_bonus += 1
        
        # 计算总等级
        total_level = base_level + match_bonus + high_freq_bonus
        
        # 限制在1-6范围内
        return max(1, min(total_level, self.max_level))
    
    def analyse_lyric(self, lines: List[str], mark_breath: bool = True) -> Tuple[List['LineResult'], float, str]:
        """
        分析整段歌词
        
        Args:
            lines: 歌词行列表
            mark_breath: 是否添加换气标记
            
        Returns:
            (行结果列表, 平均押韵密度, 总结文本)
        """
        from .schemas import LineResult
        
        if not lines:
            return [], 0.0, "空歌词"
        
        results = []
        total_density = 0.0
        context_finals = []  # 用于记录上下文的韵母
        
        for idx, line in enumerate(lines):
            # 计算本行押韵
            rhyme_unit = self.calc_line_rhyme(line, context_finals)
            
            # 更新上下文韵母
            if rhyme_unit.rhymes:
                context_finals.extend(rhyme_unit.rhymes)
            
            # 生成换气标记文本
            breath_mark = None
            if mark_breath:
                breath_mark = self._add_breath_mark(line)
            
            # 构建结果
            line_result = LineResult(
                line_index=idx,
                text=line,
                rhyme=rhyme_unit,
                breath_mark=breath_mark
            )
            results.append(line_result)
            
            total_density += rhyme_unit.density
        
        # 计算平均押韵密度
        avg_density = round(total_density / len(lines), 3) if lines else 0.0
        
        # 生成总结
        summary = self._generate_summary(lines, results, avg_density)
        
        return results, avg_density, summary
    
    def _add_breath_mark(self, text: str) -> str:
        """
        添加换气标记
        
        Args:
            text: 文本
            
        Returns:
            带换气标记的文本
        """
        chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fa5')
        
        if chinese_count <= 8:
            return text
        
        # 每8个汉字插入标记
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
    
    def _generate_summary(self, lines: List[str], results: List['LineResult'], avg_density: float) -> str:
        """
        生成分析总结
        
        Args:
            lines: 原始行列表
            results: 分析结果
            avg_density: 平均押韵密度
            
        Returns:
            总结文本
        """
        rhyme_lines = sum(1 for r in results if r.rhyme and r.rhyme.level > 0)
        total_lines = len(lines)
        
        summary = f"共{total_lines}行，{rhyme_lines}行有押韵，平均押韵密度{avg_density:.3f}"
        
        # 找出最佳押韵行
        best_line = None
        best_level = 0
        for r in results:
            if r.rhyme and r.rhyme.level > best_level:
                best_level = r.rhyme.level
                best_line = r
        
        if best_line:
            summary += f"，最佳押韵在第{best_line.line_index + 1}行（等级{best_level}）"
        
        return summary