from flask import Blueprint, render_template, redirect, url_for, request
from app.models import db, ChapterRule, NovelChapterRule
from app.auth import login_required

rules_bp = Blueprint('rules', __name__, url_prefix='/rules')


@rules_bp.route('/')
@login_required
def list():
    rules = ChapterRule.query.filter_by(enabled=True).order_by(ChapterRule.sort_order).all()
    return render_template('rules/list.html', rules=rules)


@rules_bp.route('/create', methods=['POST'])
@login_required
def create():
    name = request.form.get('name')
    pattern = request.form.get('pattern')
    category = request.form.get('category')
    description = request.form.get('description')
    enabled = bool(request.form.get('enabled', True))
    
    rule = ChapterRule(name=name, pattern=pattern, category=category, 
                       description=description, enabled=enabled)
    db.session.add(rule)
    db.session.commit()
    
    return redirect(url_for('rules.list'))


@rules_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    rule = ChapterRule.query.get_or_404(id)
    rule.name = request.form.get('name')
    rule.pattern = request.form.get('pattern')
    rule.category = request.form.get('category')
    rule.description = request.form.get('description')
    rule.enabled = bool(request.form.get('enabled'))
    db.session.commit()
    
    return redirect(url_for('rules.list'))


@rules_bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
def toggle(id):
    rule = ChapterRule.query.get_or_404(id)
    rule.enabled = not rule.enabled
    db.session.commit()
    
    return redirect(url_for('rules.list'))


@rules_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    rule = ChapterRule.query.get_or_404(id)
    db.session.delete(rule)
    db.session.commit()
    
    return redirect(url_for('rules.list'))