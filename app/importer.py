import os
import re
import chardet
from flask import Blueprint, render_template, redirect, url_for, request, session
from werkzeug.utils import secure_filename
from app.models import db, Novel, Chapter, ChapterRule, Category
from app.auth import login_required
from app.utils import DEFAULT_RULES, get_best_pattern, split_chapters, split_by_fixed_length

importer_bp = Blueprint('importer', __name__, url_prefix='/novels/import')

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')


@importer_bp.route('', methods=['GET', 'POST'])
@login_required
def step1():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            return render_template('import/step1.html', error='No file selected')

        filename = secure_filename(file.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        raw_name = os.path.splitext(file.filename)[0] if file.filename else ''
        session['import_original_filename'] = raw_name

        raw_data = open(filepath, 'rb').read()
        detected = chardet.detect(raw_data)
        encoding = detected.get('encoding', 'utf-8')

        with open(filepath, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()

        # 移除 BOM 头
        if content and content[0] == '\ufeff':
            content = content[1:]

        utf8_path = filepath + '.utf8'
        with open(utf8_path, 'w', encoding='utf-8') as f:
            f.write(content)

        session['import_filepath'] = utf8_path
        session['import_filename'] = os.path.splitext(filename)[0]

        return redirect(url_for('importer.step2'))

    return render_template('import/step1.html')


@importer_bp.route('/step2', methods=['GET', 'POST'])
@login_required
def step2():
    if 'import_filepath' not in session:
        return redirect(url_for('importer.step1'))

    system_rules = ChapterRule.query.filter_by(category='系统').order_by(ChapterRule.sort_order).all()
    user_rules = ChapterRule.query.filter_by(category='用户').order_by(ChapterRule.sort_order).all()
    enhanced_rules = ChapterRule.query.filter_by(category='增强').order_by(ChapterRule.sort_order).all()

    if request.method == 'POST':
        mode = request.form.get('mode', 'auto')

        if mode == 'auto':
            # 自动检测最佳规则
            filepath = session['import_filepath']
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            best_rule, best_pattern, match_count = get_best_pattern(content)

            if best_pattern is None:
                # 未找到合适规则，使用固定长度兜底
                session['import_fallback'] = True
                session['import_chapter_count'] = 0
                return redirect(url_for('importer.step3'))

            session['import_rule_ids'] = [str(best_rule.id)] if best_rule else []
            session['import_pattern'] = best_pattern.pattern if best_pattern else ''
            session['import_detected_rule'] = best_rule.name if best_rule else '未知'
            session['import_detected_count'] = match_count
            session['import_fallback'] = False
        else:
            # 手动选择规则
            rule_ids = request.form.getlist('rule_ids')
            custom_pattern = request.form.get('custom_pattern')

            patterns = []
            if custom_pattern:
                patterns.append(custom_pattern)
            if rule_ids:
                for rid in rule_ids:
                    if rid:
                        rule = ChapterRule.query.get(int(rid))
                        if rule:
                            patterns.append(rule.pattern)

            if not patterns:
                patterns = [DEFAULT_RULES[0]['pattern']]

            combined_pattern = '|'.join(f'(?:{p})' for p in patterns)
            session['import_pattern'] = combined_pattern
            session['import_rule_ids'] = rule_ids
            session['import_fallback'] = False

        filepath = session['import_filepath']
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if session.get('import_fallback'):
            # 固定长度兜底
            chapters = split_by_fixed_length(content)
            session['import_chapter_titles'] = [{'title': t, 'index': i} for i, (t, _) in enumerate(chapters)]
        else:
            pattern = session.get('import_pattern', '')
            try:
                compiled = re.compile(pattern, re.MULTILINE)
            except re.error:
                compiled = re.compile(DEFAULT_RULES[0]['pattern'], re.MULTILINE)

            lines = content.split('\n')
            chapter_titles = []
            for line in lines:
                line = line.strip()
                if line and compiled.match(line):
                    chapter_titles.append(line)

            session['import_chapter_titles'] = [{'title': t, 'index': i} for i, t in enumerate(chapter_titles)]

        return redirect(url_for('importer.step3'))

    return render_template('import/step2.html',
                           system_rules=system_rules,
                           user_rules=user_rules,
                           enhanced_rules=enhanced_rules)


@importer_bp.route('/step3', methods=['GET', 'POST'])
@login_required
def step3():
    if 'import_chapter_titles' not in session:
        return redirect(url_for('importer.step1'))

    chapter_titles = session.get('import_chapter_titles', [])

    if request.method == 'POST':
        delete_index = request.form.get('delete_index')
        if delete_index is not None:
            idx = int(delete_index)
            chapter_titles = [t for i, t in enumerate(chapter_titles) if i != idx]
            session['import_chapter_titles'] = chapter_titles
            return render_template('import/step3.html', chapter_titles=chapter_titles)

        return redirect(url_for('importer.step4'))

    return render_template('import/step3.html', chapter_titles=chapter_titles)


@importer_bp.route('/step4', methods=['GET', 'POST'])
@login_required
def step4():
    if 'import_chapter_titles' not in session:
        return redirect(url_for('importer.step1'))

    if request.method == 'POST':
        title = request.form.get('title', session.get('import_filename', 'Untitled'))
        author = request.form.get('author', '')
        category_id = request.form.get('category_id')

        filepath = session['import_filepath']
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        is_fallback = session.get('import_fallback', False)
        pattern = session.get('import_pattern', '')

        if is_fallback:
            chapters = split_by_fixed_length(content)
        elif not pattern:
            chapters = split_by_fixed_length(content)
        else:
            # 重新从 rule_ids 构建：每个模式转为非捕获组再组合，避免内部捕获组扰乱
            rule_ids = session.get('import_rule_ids', [])
            if rule_ids:
                db_patterns = []
                for rid in rule_ids:
                    if rid:
                        rule = ChapterRule.query.get(int(rid))
                        if rule:
                            db_patterns.append(rule.pattern)
                if db_patterns:
                    pattern = '|'.join(f'(?:{p})' for p in db_patterns)

            try:
                compiled = re.compile(pattern, re.MULTILINE)
            except re.error:
                compiled = re.compile(DEFAULT_RULES[0]['pattern'], re.MULTILINE)

            chapters = split_chapters(content, compiled)

        novel = Novel(title=title, author=author.strip() if author else None)
        if category_id:
            novel.category_id = int(category_id)
        db.session.add(novel)
        db.session.commit()

        chapter_order = 0
        for ch_title, ch_body in chapters:
            chapter_order += 1
            ch = Chapter(
                novel_id=novel.id,
                title=ch_title,
                content=ch_body,
                order=chapter_order,
                word_count=len(ch_body)
            )
            db.session.add(ch)

        novel.chapter_count = chapter_order
        novel.word_count = sum(len(c.content) for c in novel.chapters)
        db.session.commit()

        session.pop('import_filepath', None)
        session.pop('import_filename', None)
        session.pop('import_original_filename', None)
        session.pop('import_pattern', None)
        session.pop('import_chapter_titles', None)
        session.pop('import_rule_ids', None)
        session.pop('import_fallback', None)
        session.pop('import_detected_rule', None)
        session.pop('import_detected_count', None)

        return redirect(url_for('novels.detail', id=novel.id))

    chapter_count = len(session.get('import_chapter_titles', []))
    categories = Category.query.order_by(Category.sort_order).all()
    import_filename = session.get('import_original_filename', '')
    detected_rule = session.get('import_detected_rule', '')
    detected_count = session.get('import_detected_count', 0)
    is_fallback = session.get('import_fallback', False)
    return render_template('import/step4.html',
                           chapter_count=chapter_count,
                           categories=categories,
                           import_filename=import_filename,
                           detected_rule=detected_rule,
                           detected_count=detected_count,
                           is_fallback=is_fallback)