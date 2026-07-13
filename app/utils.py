from app.models import db, ChapterRule, Rating
import math


DEFAULT_RULES = [
    {'name': '中文数字章节', 'pattern': '^第[零一二三四五六七八九十百千万\\d]+章.*$', 'category': 'chinese-number', 'description': '匹配中文数字章节，如：第一章、第1章、第一百章'},
    {'name': '中文数字节', 'pattern': '^第[零一二三四五六七八九十百千万\\d]+节.*$', 'category': 'chinese-number', 'description': '匹配中文数字节，如：第一节、第1节'},
    {'name': '中文数字回', 'pattern': '^第[零一二三四五六七八九十百千万\\d]+回.*$', 'category': 'chinese-number', 'description': '匹配中文数字回，如：第一回、第1回'},
    {'name': '特殊章节', 'pattern': '^(序章|楔子|终章|后记|尾声|番外|前言|正文).*$', 'category': 'special-chapter', 'description': '匹配特殊章节名称'},
    {'name': '英文章节', 'pattern': '^(Chapter|Section|Part|Episode|No\\.)\\s*\\d+.*$', 'category': 'english-number', 'description': '匹配英文章节，如：Chapter 1、Section 2'},
    {'name': '纯数字章节', 'pattern': '^\\d+\\.?\\s*.*$', 'category': 'pure-number', 'description': '匹配纯数字章节，如：1、1.、1 开始'},
    {'name': '卷部篇', 'pattern': '^(卷|部|篇|回|场|话|集)\\s*[零一二三四五六七八九十百千万\\d]+.*$', 'category': 'volume-part', 'description': '匹配卷、部、篇等'},
    {'name': '分节阅读', 'pattern': '^分[页节章段]阅读|第\\d+[页节].*$', 'category': 'section-read', 'description': '匹配分节阅读格式'},
]


def init_default_rules():
    existing_rules = ChapterRule.query.all()
    if existing_rules:
        return

    for idx, rule_data in enumerate(DEFAULT_RULES):
        rule = ChapterRule(
            name=rule_data['name'],
            pattern=rule_data['pattern'],
            category=rule_data['category'],
            description=rule_data['description'],
            is_default=True,
            sort_order=idx
        )
        db.session.add(rule)
    
    db.session.commit()


def calculate_average_rating(novel_id):
    ratings = Rating.query.filter_by(novel_id=novel_id).all()
    
    if not ratings:
        return 0
    
    total_score = sum(r.score for r in ratings)
    average = total_score / len(ratings)
    rounded = int(round(average))
    
    return max(1, min(5, rounded))