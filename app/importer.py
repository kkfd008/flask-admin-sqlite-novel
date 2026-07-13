import os
import re
import chardet
from flask import Blueprint, render_template, redirect, url_for, request, session
from werkzeug.utils import secure_filename
from app.models import db, Novel, Chapter, ChapterRule
from app.auth import login_required
from app.utils import DEFAULT_RULES

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

        raw_data = open(filepath, 'rb').read()
        detected = chardet.detect(raw_data)
        encoding = detected.get('encoding', 'utf-8')

        with open(filepath, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()

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

    if request.method == 'POST':
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

        filepath = session['import_filepath']
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        chapter_titles = []
        for line in lines:
            line = line.strip()
            if line and re.match(combined_pattern, line):
                chapter_titles.append(line)

        session['import_pattern'] = combined_pattern
        session['import_chapter_titles'] = [{'title': t, 'index': i} for i, t in enumerate(chapter_titles)]

        return redirect(url_for('importer.step3'))

    return render_template('import/step2.html',
                           system_rules=system_rules,
                           user_rules=user_rules)


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

        pattern = session.get('import_pattern', '')

        novel = Novel(title=title, author=author if author else None)
        if category_id:
            novel.category_id = int(category_id)
        db.session.add(novel)
        db.session.commit()

        parts = re.split(f'({pattern})', content, flags=re.MULTILINE)

        chapter_order = 0
        preamble = parts[0].strip() if parts else ''
        if preamble:
            chapter_order += 1
            ch = Chapter(novel_id=novel.id, title='序章', content=preamble, order=chapter_order)
            db.session.add(ch)

        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                ch_title = parts[i].strip()
                ch_content = parts[i + 1].strip()
                chapter_order += 1
                ch = Chapter(novel_id=novel.id, title=ch_title, content=ch_content, order=chapter_order)
                db.session.add(ch)

        novel.chapter_count = chapter_order
        novel.word_count = sum(len(c.content) for c in novel.chapters)
        db.session.commit()

        session.pop('import_filepath', None)
        session.pop('import_filename', None)
        session.pop('import_pattern', None)
        session.pop('import_chapter_titles', None)

        return redirect(url_for('novels.detail', id=novel.id))

    chapter_count = len(session.get('import_chapter_titles', []))
    return render_template('import/step4.html', chapter_count=chapter_count)