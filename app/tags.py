from flask import Blueprint, render_template, redirect, url_for, request
from app.models import db, Tag, Novel
from app.auth import login_required

tags_bp = Blueprint('tags', __name__, url_prefix='/tags')


@tags_bp.route('/')
@login_required
def list():
    tags = Tag.query.all()
    return render_template('tags/list.html', tags=tags)


@tags_bp.route('/create', methods=['POST'])
@login_required
def create():
    name = request.form.get('name')
    color = request.form.get('color', '#1E9FFF')
    
    tag = Tag(name=name, color=color)
    db.session.add(tag)
    db.session.commit()
    
    return redirect(url_for('tags.list'))


@tags_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    tag = Tag.query.get_or_404(id)
    tag.name = request.form.get('name')
    tag.color = request.form.get('color')
    db.session.commit()
    
    return redirect(url_for('tags.list'))


@tags_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    tag = Tag.query.get_or_404(id)
    db.session.delete(tag)
    db.session.commit()
    
    return redirect(url_for('tags.list'))