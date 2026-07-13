from flask import Blueprint, render_template, redirect, url_for, request
from app.models import db, Category
from app.auth import login_required

categories_bp = Blueprint('categories', __name__, url_prefix='/categories')


@categories_bp.route('/')
@login_required
def list():
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('categories/list.html', categories=categories)


@categories_bp.route('/create', methods=['POST'])
@login_required
def create():
    name = request.form.get('name')
    description = request.form.get('description')
    sort_order = int(request.form.get('sort_order', 0))
    
    category = Category(name=name, description=description, sort_order=sort_order)
    db.session.add(category)
    db.session.commit()
    
    return redirect(url_for('categories.list'))


@categories_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    category = Category.query.get_or_404(id)
    category.name = request.form.get('name')
    category.description = request.form.get('description')
    category.sort_order = int(request.form.get('sort_order', 0))
    db.session.commit()
    
    return redirect(url_for('categories.list'))


@categories_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    category = Category.query.get_or_404(id)
    
    from app.models import Novel
    Novel.query.filter_by(category_id=id).update({'category_id': None})
    
    db.session.delete(category)
    db.session.commit()
    
    return redirect(url_for('categories.list'))