import os
import re
import shutil
import chardet
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, session
from app.models import db, Novel, Chapter, ChapterRule, Category, Upload, NovelChapterRule, Favorite, Rating, ReadingProgress, Bookmark
from app.auth import login_required
from app.utils import DEFAULT_RULES, get_best_pattern, split_chapters, split_by_fixed_length

importer_bp = Blueprint('importer', __name__, url_prefix='/novels/import')

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')


@importer_bp.route('', methods=['GET', 'POST'])
@login_required
def step1():
    if request.method == 'POST':
        file = request.files.get('file')
        overwrite = request.form.get('overwrite')
        temp_path = None
        existing = None

        # 覆盖提交：从临时文件恢复
        if overwrite and not file:
            temp_path = session.get('import_temp_file')
            if not temp_path or not os.path.exists(temp_path):
                return render_template('import/step1.html', error='临时文件已过期，请重新上传')
            raw_name = session.get('import_temp_raw_name', '')
            filename = session.get('import_temp_filename', '')
            if not raw_name or not filename:
                return render_template('import/step1.html', error='会话已过期，请重新上传')
            file_size = os.path.getsize(temp_path)
            existing = Upload.query.filter_by(title=raw_name).first()
        else:
            if not file:
                return render_template('import/step1.html', error='No file selected')

            raw_name = os.path.splitext(file.filename)[0] if file.filename else ''
            original_ext = os.path.splitext(file.filename)[1] if file.filename else '.txt'
            saved_filename = raw_name + original_ext

            file_content = file.read()
            file_size = len(file_content)
            file.seek(0)

            existing = Upload.query.filter_by(title=raw_name).first()
            if existing and not overwrite:
                # 保存临时文件用于覆盖提交
                temp_dir = os.path.join(UPLOAD_FOLDER, '.temp')
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, saved_filename)
                file.save(temp_path)
                session['import_temp_file'] = temp_path
                session['import_temp_raw_name'] = raw_name
                session['import_temp_filename'] = saved_filename

                return render_template('import/step1.html',
                                       duplicate=True,
                                       existing=existing,
                                       new_filename=saved_filename,
                                       new_size=file_size,
                                       error=None)

        if existing and overwrite:
            # 覆盖原书籍和章节
            if existing.novel_id and request.form.get('overwrite_novel'):
                old_novel = Novel.query.get(existing.novel_id)
                if old_novel:
                    Chapter.query.filter_by(novel_id=old_novel.id).delete()
                    NovelChapterRule.query.filter_by(novel_id=old_novel.id).delete()
                    Favorite.query.filter_by(novel_id=old_novel.id).delete()
                    Rating.query.filter_by(novel_id=old_novel.id).delete()
                    ReadingProgress.query.filter_by(novel_id=old_novel.id).delete()
                    Bookmark.query.filter_by(novel_id=old_novel.id).delete()
                    db.session.delete(old_novel)
                    db.session.commit()
                    existing.novel_id = 0
                    db.session.commit()

            # 覆盖：保持原路径，更新文件内容和元数据
            filepath = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                existing.file_path
            )
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            if temp_path:
                shutil.copy(temp_path, filepath)
            else:
                file.save(filepath)
            existing.file_size = file_size
            existing.updated_at = datetime.now()
            db.session.commit()
            session['import_upload_id'] = existing.id
        else:
            # 新文件
            date_dir = datetime.now().strftime('%y%m%d')
            date_folder = os.path.join(UPLOAD_FOLDER, date_dir)
            os.makedirs(date_folder, exist_ok=True)

            filepath = os.path.join(date_folder, saved_filename)
            if temp_path:
                shutil.copy(temp_path, filepath)
            else:
                file.save(filepath)

            rel_path = os.path.join('uploads', date_dir, saved_filename)
            upload = Upload(title=raw_name, file_path=rel_path, file_size=file_size)
            db.session.add(upload)
            db.session.commit()
            session['import_upload_id'] = upload.id

        session['import_original_filename'] = raw_name

        raw_data = open(filepath, 'rb').read()
        detected = chardet.detect(raw_data)
        encoding = detected.get('encoding', 'utf-8')

        with open(filepath, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()

        if content and content[0] == '\ufeff':
            content = content[1:]

        utf8_path = filepath + '.utf8'
        with open(utf8_path, 'w', encoding='utf-8') as f:
            f.write(content)

        session['import_filepath'] = utf8_path
        session['import_filename'] = raw_name

        # 清理临时文件
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        session.pop('import_temp_file', None)
        session.pop('import_temp_raw_name', None)
        session.pop('import_temp_filename', None)

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
            session['import_chapters'] = [{'title': t, 'content': c} for t, c in chapters]
        else:
            pattern = session.get('import_pattern', '')
            try:
                compiled = re.compile(pattern, re.MULTILINE)
            except re.error:
                compiled = re.compile(DEFAULT_RULES[0]['pattern'], re.MULTILINE)

            results = split_chapters(content, compiled)
            session['import_chapters'] = [{'title': t, 'content': c} for t, c in results]

        return redirect(url_for('importer.step3'))

    return render_template('import/step2.html',
                           system_rules=system_rules,
                           user_rules=user_rules,
                           enhanced_rules=enhanced_rules)


@importer_bp.route('/step3', methods=['GET', 'POST'])
@login_required
def step3():
    if 'import_chapters' not in session:
        return redirect(url_for('importer.step1'))

    chapters = session.get('import_chapters', [])

    if request.method == 'POST':
        delete_index = request.form.get('delete_index')
        if delete_index is not None:
            idx = int(delete_index)
            if 0 < idx < len(chapters):
                # 将被删除章节的内容合并到上一章
                chapters[idx - 1]['content'] += '\n' + chapters[idx]['content']
            chapters.pop(idx)
            session['import_chapters'] = chapters
            session.modified = True
            chapter_titles = [c['title'] for c in chapters]
            return render_template('import/step3.html', chapter_titles=chapter_titles)

        return redirect(url_for('importer.step4'))

    chapter_titles = [c['title'] for c in chapters]
    return render_template('import/step3.html', chapter_titles=chapter_titles)


@importer_bp.route('/step4', methods=['GET', 'POST'])
@login_required
def step4():
    if 'import_chapters' not in session:
        return redirect(url_for('importer.step1'))

    if request.method == 'POST':
        title = request.form.get('title', session.get('import_filename', 'Untitled'))
        author = request.form.get('author', '')
        category_id = request.form.get('category_id')

        chapters = session.get('import_chapters', [])

        novel = Novel(title=title, author=author.strip() if author else None)
        if category_id:
            novel.category_id = int(category_id)
        db.session.add(novel)
        db.session.commit()

        chapter_order = 0
        for ch_data in chapters:
            chapter_order += 1
            ch = Chapter(
                novel_id=novel.id,
                title=ch_data['title'],
                content=ch_data['content'],
                order=chapter_order,
                word_count=len(ch_data['content'])
            )
            db.session.add(ch)

        novel.chapter_count = chapter_order
        novel.word_count = sum(len(c.content) for c in novel.chapters)
        db.session.commit()

        # 更新上传记录的 novel_id
        upload_id = session.get('import_upload_id')
        if upload_id:
            upload = Upload.query.get(upload_id)
            if upload:
                upload.novel_id = novel.id
                upload.last_import_at = datetime.now()
                db.session.commit()

        session.pop('import_filepath', None)
        session.pop('import_filename', None)
        session.pop('import_original_filename', None)
        session.pop('import_upload_id', None)
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