from app.models import db, ChapterRule, Rating
import chardet
import math
import os
import re


def utf8_path_for(src_path, utf8_dir, upload_root):
    """返回源文件对应的 utf8 副本路径（不保证文件存在）。

    与 convert_file_to_utf8 的命名规则一致：保留相对 upload_root 的目录结构，
    例如 uploads/260919/book/a.txt → utf8/260919/book/a.txt。
    """
    rel_path = os.path.relpath(src_path, upload_root)
    # 源文件不在上传根目录内时，退化为仅保留文件名
    if rel_path.startswith('..'):
        rel_path = os.path.basename(src_path)
    return os.path.join(utf8_dir, rel_path)


def convert_file_to_utf8(src_path, utf8_dir, upload_root):
    """将源文件内容转换为 UTF-8 编码，保存到 utf8 目录。

    保留与 upload_root（上传根目录）相同的相对目录结构，
    例如 uploads/260919/book/a.txt → utf8/260919/book/a.txt。

    返回转换后文件的绝对路径。
    """
    dest_path = utf8_path_for(src_path, utf8_dir, upload_root)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    with open(src_path, 'rb') as f:
        raw = f.read()

    has_bom = raw.startswith(b'\xef\xbb\xbf')

    def decode(enc, errors='strict'):
        try:
            return raw.decode(enc, errors=errors)
        except (UnicodeDecodeError, LookupError):
            return None

    # 1. 用 chardet 检测编码（取前 1MB 样本）
    detected_enc = None
    try:
        d = chardet.detect(raw[:1024 * 1024])
        if d.get('confidence', 0.0) >= 0.5 and d.get('encoding'):
            detected_enc = d['encoding'].lower()
    except Exception:
        detected_enc = None

    # 2. 归一化编码名：GB 系列统一用 GB18030（GBK/GB2312 超集）
    enc = None
    if detected_enc:
        if detected_enc in ('utf-8', 'utf-8-sig', 'utf8', 'ascii'):
            enc = 'utf-8-sig' if has_bom else 'utf-8'
        elif detected_enc in ('gb2312', 'gbk', 'gb18030', 'gb-2312'):
            enc = 'gb18030'
        elif detected_enc in ('big5', 'big-5'):
            enc = 'big5'
        else:
            enc = detected_enc

    # 3. 解码：优先严格；UTF-8 文件若末尾损坏则容错解码以保留正文
    text = None
    if enc:
        text = decode(enc)
        if text is None:
            text = decode(enc, errors='replace')

    # 4. 回退：UTF-8 → GB18030
    if text is None:
        text = decode('utf-8-sig' if has_bom else 'utf-8')
    if text is None:
        text = decode('gb18030')

    # 5. 最终兜底（永不抛异常）
    if text is None:
        text = decode('utf-8', errors='replace')

    with open(dest_path, 'wb') as f:
        f.write(text.encode('utf-8'))

    return dest_path


DEFAULT_RULES = [
    {'name': '中文数字章节', 'pattern': '^第[零一二三四五六七八九十百千万\\d]+章.*$', 'category': '系统', 'description': '匹配中文数字章节，如：第一章、第1章、第一百章'},
    {'name': '中文数字节', 'pattern': '^第[零一二三四五六七八九十百千万\\d]+节.*$', 'category': '系统', 'description': '匹配中文数字节，如：第一节、第1节'},
    {'name': '中文数字回', 'pattern': '^第[零一二三四五六七八九十百千万\\d]+回.*$', 'category': '系统', 'description': '匹配中文数字回，如：第一回、第1回'},
    {'name': '特殊章节', 'pattern': '^(序章|楔子|终章|后记|尾声|番外|前言|正文).*$', 'category': '系统', 'description': '匹配特殊章节名称'},
    {'name': '英文章节', 'pattern': '^(Chapter|Section|Part|Episode|No\\.)\\s*\\d+.*$', 'category': '系统', 'description': '匹配英文章节，如：Chapter 1、Section 2'},
    {'name': '纯数字章节', 'pattern': '^\\d+\\.?\\s*.*$', 'category': '系统', 'description': '匹配纯数字章节，如：1、1.、1 开始'},
    {'name': '卷部篇', 'pattern': '^(卷|部|篇|回|场|话|集)\\s*[零一二三四五六七八九十百千万\\d]+.*$', 'category': '系统', 'description': '匹配卷、部、篇等'},
    {'name': '分节阅读', 'pattern': '^分[页节章段]阅读|第\\d+[页节].*$', 'category': '系统', 'description': '匹配分节阅读格式'},
]

# Legado 增强规则（25条），参考 split_txt_novel.py 的 TXT_TOC_RULES
# 涵盖更全面的章节匹配场景：中文数字（含壹贰叁）、英文、分隔符、特殊符号、双标题等
LEGADO_ENHANCED_RULES = [
    # -1: 目录(去空白) — 宽松匹配，前面有空白即可
    {
        'name': '目录(去空白)',
        'pattern': r'(?<=[　\s])(?:序章|楔子|正文(?!完|结)|终章|后记|尾声|番外|第\s{0,4}[\d〇零一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟]+?\s{0,4}(?:章|节(?!课)|卷|集(?![合和]))).{0,30}$',
        'category': '增强',
        'description': 'Legado规则：宽松匹配，前面有空白即可匹配章节',
    },
    # -2: 目录 — 行首匹配
    {
        'name': '目录',
        'pattern': r'^[ 　\t]{0,4}(?:序章|楔子|正文(?!完|结)|终章|后记|尾声|番外|第\s{0,4}[\d〇零一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟]+?\s{0,4}(?:章|节(?!课)|卷|集(?![合和])|部(?![分赛游])|篇(?!张))).{0,30}$',
        'category': '增强',
        'description': 'Legado规则：行首匹配章节（含卷/部/篇）',
    },
    # -8: 数字 分隔符 标题名称
    {
        'name': '数字分隔符标题',
        'pattern': r'^[ 　\t]{0,4}\d{1,5}[:：,.， 、_—\-].{1,30}$',
        'category': '增强',
        'description': 'Legado规则：数字 + 分隔符 + 标题名称',
    },
    # -9: 大写数字 分隔符 标题名称
    {
        'name': '中文数字分隔符标题',
        'pattern': r'^[ 　\t]{0,4}(?:序章|楔子|正文(?!完|结)|终章|后记|尾声|番外|[零一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟]{1,8}章?)[ 、_—\-].{1,30}$',
        'category': '增强',
        'description': 'Legado规则：中文数字/特殊章节 + 分隔符 + 标题',
    },
    # -11: 正文 标题/序号
    {
        'name': '正文标题',
        'pattern': r'^[ 　\t]{0,4}正文[ 　]{1,4}.{0,20}$',
        'category': '增强',
        'description': 'Legado规则：正文 + 空格 + 标题',
    },
    # -12: Chapter/Section/Part/Episode 序号 标题
    {
        'name': '英文章节(增强)',
        'pattern': r'^[ 　\t]{0,4}(?:[Cc]hapter|[Ss]ection|[Pp]art|ＰＡＲＴ|[Nn][oO][.、]|[Ee]pisode|(?:内容|文章)?简介|文案|前言|序章|楔子|正文(?!完|结)|终章|后记|尾声|番外)\s{0,4}\d{1,4}.{0,30}$',
        'category': '增强',
        'description': 'Legado规则：英文 + 特殊章节 + 序号 + 标题',
    },
    # -14: 特殊符号 序号 标题
    {
        'name': '特殊符号序号标题',
        'pattern': r'(?<=[\s　])[【〔〖「『〈［\[](?:第|[Cc]hapter)[\d零一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟]{1,10}[章节].{0,20}$',
        'category': '增强',
        'description': 'Legado规则：特殊符号 + 序号 + 标题',
    },
    # -16: 特殊符号 标题(单个)
    {
        'name': '特殊符号标题',
        'pattern': r'(?<=[\s　]{0,4})(?:[☆★✦✧].{1,30}|(?:内容|文章)?简介|文案|前言|序章|楔子|正文(?!完|结)|终章|后记|尾声|番外)[ 　]{0,4}$',
        'category': '增强',
        'description': 'Legado规则：特殊符号 + 标题',
    },
    # -17: 章/卷 序号 标题
    {
        'name': '章卷序号标题',
        'pattern': r'^[ \t　]{0,4}(?:(?:内容|文章)?简介|文案|前言|序章|楔子|正文(?!完|结)|终章|后记|尾声|番外|[卷章][\d零一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟]{1,8})[ 　]{0,4}.{0,30}$',
        'category': '增强',
        'description': 'Legado规则：章/卷 + 序号 + 标题',
    },
    # -21: 书名 括号 序号
    {
        'name': '书名括号序号',
        'pattern': r'^[一-龥]{1,20}[ 　\t]{0,4}[(（][\d〇零一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟]{1,8}[)）][ 　\t]{0,4}$',
        'category': '增强',
        'description': 'Legado规则：书名 + 括号 + 序号',
    },
    # -22: 书名 序号
    {
        'name': '书名序号',
        'pattern': r'^[一-龥]{1,20}[ 　\t]{0,4}[\d〇零一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟]{1,8}[ 　\t]{0,4}$',
        'category': '增强',
        'description': 'Legado规则：书名 + 序号',
    },
    # -24: 字数分割 分节阅读
    {
        'name': '分节阅读(增强)',
        'pattern': r'(?<=[ 　\t]{0,4})(?:.{0,15}分[页节章段]阅读[-_ ]|第\s{0,4}[\d零一二两三四五六七八九十百千万]{1,6}\s{0,4}[页节]).{0,30}$',
        'category': '增强',
        'description': 'Legado规则：分节阅读 + 字数分割',
    },
    # -25: 通用规则
    {
        'name': '通用规则',
        'pattern': r'(?im)^.{0,6}(?:[引楔]子|正文(?!完|结)|[引序前]言|[序终]章|扉页|[上中下][部篇卷]|卷首语|后记|尾声|番外|={2,4}|第\s{0,4}[\d〇零一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟]+?\s{0,4}(?:章|节(?!课)|卷|页[、 　]|集(?![合和])|部(?![分是门落])|篇(?!张))).{0,40}$|^.{0,6}[\d〇零一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟a-z]{1,8}[、. 　].{0,20}$',
        'category': '增强',
        'description': 'Legado规则：通用兜底规则，涵盖引子、序言、扉页、上中下等',
    },
]


def init_default_rules():
    """初始化默认规则 + 增强规则"""
    for idx, rule_data in enumerate(DEFAULT_RULES):
        existing = ChapterRule.query.filter_by(name=rule_data['name']).first()
        if existing:
            existing.category = rule_data['category']
            existing.description = rule_data['description']
            existing.sort_order = idx
        else:
            rule = ChapterRule(
                name=rule_data['name'],
                pattern=rule_data['pattern'],
                category=rule_data['category'],
                description=rule_data['description'],
                is_default=True,
                sort_order=idx
            )
            db.session.add(rule)

    # 初始化增强规则
    for idx, rule_data in enumerate(LEGADO_ENHANCED_RULES):
        existing = ChapterRule.query.filter_by(name=rule_data['name']).first()
        if existing:
            if existing.category == '系统':
                existing.category = rule_data['category']
                existing.pattern = rule_data['pattern']
                existing.description = rule_data['description']
        else:
            rule = ChapterRule(
                name=rule_data['name'],
                pattern=rule_data['pattern'],
                category=rule_data['category'],
                description=rule_data['description'],
                is_default=True,
                sort_order=len(DEFAULT_RULES) + idx
            )
            db.session.add(rule)

    db.session.commit()


def get_best_pattern(content, sample_size=100000):
    """
    自动检测最佳章节匹配规则。
    遍历所有启用的规则，找出匹配章节数最多的规则。
    参考 Legado TextFile.getTocRule() 逻辑。
    """
    sample = content[:sample_size]
    rules = ChapterRule.query.filter_by(enabled=True).order_by(ChapterRule.sort_order).all()
    rules.reverse()

    max_num = 1
    best_rule = None
    best_pattern = None

    for rule in rules:
        try:
            pattern = re.compile(rule.pattern, re.MULTILINE)
        except re.error:
            continue

        matches = list(pattern.finditer(sample))
        start = 0
        num = 0
        for m in matches:
            # 只计数距离上次匹配超过 1000 字符的匹配（避免同一章节内误匹配）
            if start == 0 or m.start() - start > 1000:
                num += 1
                start = m.end()

        if num >= max_num:
            max_num = num
            best_rule = rule
            best_pattern = pattern

    return best_rule, best_pattern, max_num


def split_chapters(content, pattern):
    """
    使用正则 pattern 分割章节。
    返回 [(章节标题, 章节内容), ...] 列表。
    参考 split_txt_novel.py 的 split_chapters() 逻辑。
    """
    chapters = []
    matches = list(pattern.finditer(content))

    if not matches:
        return [('全文', content.strip())]

    first_match = matches[0]
    if first_match.start() > 0:
        pre_content = content[:first_match.start()].strip()
        if pre_content:
            chapters.append(('序章', pre_content))

    for i, match in enumerate(matches):
        title = match.group().strip()
        start = match.start()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(content)
        chapter_content = content[start:end]
        body = chapter_content[len(match.group()):].strip()
        chapters.append((title, body))

    return _dedupe_toc(chapters)


# 目录条目的正文长度上限：正文短于此长度且标题在后面重复出现，即判定为目录条目
TOC_BODY_MAX_LEN = 30


def _dedupe_toc(chapters):
    """去掉 TXT 文件开头章节目录造成的重复条目。

    部分 TXT 在正文前附有一份章节目录，目录行会被章节规则同样匹配成
    “正文为空”的章节，导致章节数接近翻倍。这里把「标题在后面重复出现
    且自身正文极短」的条目判定为目录条目并丢弃。
    """
    if len(chapters) < 3:
        return chapters

    def normalize(title):
        return re.sub(r'\s+', '', title)

    # 每个标题最后一次出现的下标
    last_index = {}
    for i, (title, _) in enumerate(chapters):
        last_index[normalize(title)] = i

    kept = []
    dropped = 0
    for i, (title, body) in enumerate(chapters):
        is_duplicate = last_index[normalize(title)] != i
        if is_duplicate and len(body.strip()) < TOC_BODY_MAX_LEN:
            dropped += 1
            continue
        kept.append((title, body))

    # 目录块前常有一行“目录”抬头，会被切成正文极短的“序章”，一并去掉
    if dropped >= 2 and kept and kept[0][0] == '序章' and len(kept[0][1].strip()) < TOC_BODY_MAX_LEN:
        kept.pop(0)

    return kept


def split_by_fixed_length(content, max_len=10000):
    """按固定长度分割章节（兜底方案）"""
    chapters = []
    lines = content.split('\n')
    current_lines = []
    current_len = 0
    chapter_num = 1

    for line in lines:
        current_lines.append(line)
        current_len += len(line) + 1
        if current_len >= max_len:
            title = f'第{chapter_num}章'
            body = '\n'.join(current_lines)
            chapters.append((title, body))
            current_lines = []
            current_len = 0
            chapter_num += 1

    if current_lines:
        title = f'第{chapter_num}章'
        body = '\n'.join(current_lines)
        chapters.append((title, body))

    return chapters


def calculate_average_rating(novel_id):
    ratings = Rating.query.filter_by(novel_id=novel_id).all()
    
    if not ratings:
        return 0
    
    total_score = sum(r.score for r in ratings)
    average = total_score / len(ratings)
    rounded = int(round(average))
    
    return max(1, min(5, rounded))