from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.models import db, ChapterRule, NovelChapterRule
from app.auth import login_required

rules_bp = Blueprint('rules', __name__, url_prefix='/rules')


@rules_bp.route('/')
@login_required
def list():
    system_rules = ChapterRule.query.filter_by(category='系统').order_by(ChapterRule.sort_order).all()
    user_rules = ChapterRule.query.filter_by(category='用户').order_by(ChapterRule.sort_order).all()
    legado_rules = ChapterRule.query.filter_by(category='增强').order_by(ChapterRule.sort_order).all()
    return render_template('rules/list.html', system_rules=system_rules, user_rules=user_rules, legado_rules=legado_rules)


@rules_bp.route('/create', methods=['POST'])
@login_required
def create():
    name = request.form.get('name')
    pattern = request.form.get('pattern')
    description = request.form.get('description')
    enabled = bool(request.form.get('enabled', True))

    rule = ChapterRule(name=name, pattern=pattern, category='用户',
                       description=description, enabled=enabled)
    db.session.add(rule)
    db.session.commit()

    return redirect(url_for('rules.list'))


@rules_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    rule = ChapterRule.query.get_or_404(id)

    if rule.category in ('系统', '增强'):
        flash('系统规则不可修改', 'error')
        return redirect(url_for('rules.list'))

    rule.name = request.form.get('name')
    rule.pattern = request.form.get('pattern')
    rule.description = request.form.get('description')
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

    if rule.category in ('系统', '增强'):
        flash('系统规则不可删除', 'error')
        return redirect(url_for('rules.list'))

    db.session.delete(rule)
    db.session.commit()

    return redirect(url_for('rules.list'))