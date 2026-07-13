from flask import Blueprint, render_template, redirect, url_for, session
from app.models import db, Favorite, Novel
from app.auth import login_required

favorites_bp = Blueprint('favorites', __name__, url_prefix='/favorites')


@favorites_bp.route('/')
@login_required
def list():
    user_id = session.get('user_id')
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    novels = [fav.novel for fav in favorites]
    return render_template('favorites/list.html', novels=novels)


@favorites_bp.route('/novels/<int:novel_id>/favorite', methods=['POST'])
@login_required
def favorite(novel_id):
    user_id = session.get('user_id')
    existing = Favorite.query.filter_by(user_id=user_id, novel_id=novel_id).first()
    if not existing:
        fav = Favorite(user_id=user_id, novel_id=novel_id)
        db.session.add(fav)
        db.session.commit()
    return redirect(url_for('novels.detail', id=novel_id))


@favorites_bp.route('/novels/<int:novel_id>/unfavorite', methods=['POST'])
@login_required
def unfavorite(novel_id):
    user_id = session.get('user_id')
    existing = Favorite.query.filter_by(user_id=user_id, novel_id=novel_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    return redirect(url_for('novels.detail', id=novel_id))