from flask import Blueprint, render_template, redirect, url_for, request, session, send_file
from app.models import db, Novel, Chapter, Category, Tag, NovelChapterRule, Favorite, Rating, Bookmark, ReadingProgress, Upload
from app.auth import login_required
import os

novels_bp = Blueprint('novels', __name__, url_prefix='/novels')


@novels_bp.route('/')
@login_required
def list():
    category_id = request.args.get('category_id')
    tag_id = request.args.get('tag_id')
    q = (request.args.get('q') or '').strip()
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    query = Novel.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if tag_id:
        query = query.join(Novel.tags).filter(Tag.id == tag_id)
    
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(Novel.title.ilike(like), Novel.author.ilike(like)))
    
    sort_column = getattr(Novel, sort_by, Novel.created_at)
    if sort_order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    novels = query.all()
    categories = Category.query.all()
    tags = Tag.query.all()
    
    return render_template('novels/list.html', novels=novels, categories=categories, tags=tags)


@novels_bp.route('/<int:id>')
@login_required
def detail(id):
    novel = Novel.query.get_or_404(id)
    chapters = Chapter.query.filter_by(novel_id=id).order_by(Chapter.order).all()
    all_tags = Tag.query.all()
    categories = Category.query.order_by(Category.sort_order).all()
    user_id = session.get('user_id', 1)
    my_rating = Rating.query.filter_by(user_id=user_id, novel_id=id).first()
    is_favorited = Favorite.query.filter_by(user_id=user_id, novel_id=id).first() is not None
    return render_template('novels/detail.html', novel=novel, chapters=chapters,
                          all_tags=all_tags, my_rating=my_rating, is_favorited=is_favorited,
                          categories=categories)


@novels_bp.route('/<int:id>/chapter')
@login_required
def chapter_directory(id):
    novel = Novel.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    # 允许的每页选项
    if per_page not in (10, 20, 50, 100):
        per_page = 20

    pagination = Chapter.query.filter_by(novel_id=id)\
        .order_by(Chapter.order)\
        .paginate(page=page, per_page=per_page, error_out=False)

    return render_template('novels/chapters.html', novel=novel, pagination=pagination,
                          per_page=per_page, page=page)


@novels_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    novel = Novel.query.get_or_404(id)
    novel.title = request.form.get('title', novel.title)
    novel.author = request.form.get('author', '') or None
    category_id = request.form.get('category_id')
    novel.category_id = int(category_id) if category_id else None
    db.session.commit()
    return redirect(url_for('novels.detail', id=id))


@novels_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    novel = Novel.query.get_or_404(id)
    
    # 级联删除所有关联数据，避免 NOT NULL constraint 错误
    Chapter.query.filter_by(novel_id=id).delete()
    NovelChapterRule.query.filter_by(novel_id=id).delete()
    Favorite.query.filter_by(novel_id=id).delete()
    Rating.query.filter_by(novel_id=id).delete()
    Bookmark.query.filter_by(novel_id=id).delete()
    ReadingProgress.query.filter_by(novel_id=id).delete()
    
    # 反查上传表，将 novel_id 重置为 0
    Upload.query.filter_by(novel_id=id).update({'novel_id': 0})
    
    db.session.delete(novel)
    db.session.commit()
    
    return redirect(url_for('novels.list'))


@novels_bp.route('/<int:id>/tags', methods=['POST'])
@login_required
def update_tags(id):
    novel = Novel.query.get_or_404(id)
    tag_ids = request.form.getlist('tag_ids')
    
    novel.tags = []
    for tid in tag_ids:
        tag = Tag.query.get(tid)
        if tag:
            novel.tags.append(tag)
    
    db.session.commit()
    
    return redirect(url_for('novels.detail', id=id))


@novels_bp.route('/<int:id>/rules')
@login_required
def rules_list(id):
    novel = Novel.query.get_or_404(id)
    rules = NovelChapterRule.query.filter_by(novel_id=id).all()
    return render_template('novels/rules.html', novel=novel, rules=rules)


@novels_bp.route('/<int:id>/rules/create', methods=['POST'])
@login_required
def rules_create(id):
    novel = Novel.query.get_or_404(id)
    
    existing_rule = NovelChapterRule.query.filter_by(novel_id=id).first()
    if existing_rule:
        existing_rule.pattern = request.form.get('pattern')
        existing_rule.description = request.form.get('description')
    else:
        rule = NovelChapterRule(novel_id=id, pattern=request.form.get('pattern'),
                               description=request.form.get('description'))
        db.session.add(rule)
    
    db.session.commit()
    
    return redirect(url_for('novels.rules_list', id=id))


@novels_bp.route('/<int:id>/rules/<int:rule_id>/edit', methods=['POST'])
@login_required
def rules_edit(id, rule_id):
    rule = NovelChapterRule.query.get_or_404(rule_id)
    rule.pattern = request.form.get('pattern')
    rule.description = request.form.get('description')
    db.session.commit()
    
    return redirect(url_for('novels.rules_list', id=id))


@novels_bp.route('/<int:id>/rules/<int:rule_id>/delete', methods=['POST'])
@login_required
def rules_delete(id, rule_id):
    rule = NovelChapterRule.query.get_or_404(rule_id)
    db.session.delete(rule)
    db.session.commit()
    
    return redirect(url_for('novels.rules_list', id=id))


@novels_bp.route('/uploads')
@login_required
def uploads():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    q = (request.args.get('q') or '').strip()
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')

    query = Upload.query

    if q:
        query = query.filter(Upload.title.ilike(f'%{q}%'))

    if sort_by == 'chapter_count':
        # 章节数量存放在关联的 Novel 上，用外连接保证未导入的记录也保留
        query = query.outerjoin(Novel, Upload.novel_id == Novel.id)
        sort_column = Novel.chapter_count
    elif sort_by == 'file_size':
        sort_column = Upload.file_size
    elif sort_by == 'title':
        sort_column = Upload.title
    else:
        sort_column = Upload.created_at

    if sort_order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 章节数量存放在关联的 Novel 上，这里批量取出，避免逐行查询
    novel_ids = [u.novel_id for u in pagination.items if u.novel_id]
    chapter_counts = {}
    if novel_ids:
        rows = db.session.query(Novel.id, Novel.chapter_count)\
            .filter(Novel.id.in_(novel_ids)).all()
        chapter_counts = dict(rows)

    return render_template('novels/uploads.html', pagination=pagination, q=q,
                           sort_by=sort_by, sort_order=sort_order,
                           chapter_counts=chapter_counts)


@novels_bp.route('/uploads/<int:upload_id>/download')
@login_required
def download_upload(upload_id):
    upload = Upload.query.get_or_404(upload_id)
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), upload.file_path)
    if not os.path.exists(filepath):
        return '文件不存在', 404
    return send_file(filepath, as_attachment=True, download_name=upload.title + os.path.splitext(upload.file_path)[1])