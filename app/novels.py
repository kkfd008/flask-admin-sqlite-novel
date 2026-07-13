from flask import Blueprint, render_template, redirect, url_for, request, session
from app.models import db, Novel, Category, Tag, NovelChapterRule
from app.auth import login_required

novels_bp = Blueprint('novels', __name__, url_prefix='/novels')


@novels_bp.route('/')
@login_required
def list():
    category_id = request.args.get('category_id')
    tag_id = request.args.get('tag_id')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    query = Novel.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if tag_id:
        query = query.join(Novel.tags).filter(Tag.id == tag_id)
    
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
    return render_template('novels/detail.html', novel=novel)


@novels_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    novel = Novel.query.get_or_404(id)
    
    NovelChapterRule.query.filter_by(novel_id=id).delete()
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