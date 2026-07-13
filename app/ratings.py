from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from app.models import db, Rating, Novel
from app.auth import login_required
from app.utils import calculate_average_rating

ratings_bp = Blueprint('ratings', __name__)


@ratings_bp.route('/novels/<int:novel_id>/rate', methods=['POST'])
@login_required
def rate(novel_id):
    user_id = session.get('user_id', 1)

    score_str = request.form.get('score')
    if not score_str:
        flash('请选择评分星级', 'error')
        return redirect(url_for('novels.detail', id=novel_id))

    score = int(score_str)
    comment = request.form.get('comment')
    
    existing_rating = Rating.query.filter_by(user_id=user_id, novel_id=novel_id).first()
    
    if existing_rating:
        existing_rating.score = score
        existing_rating.comment = comment
    else:
        rating = Rating(user_id=user_id, novel_id=novel_id, score=score, comment=comment)
        db.session.add(rating)
    
    db.session.commit()
    
    average_rating = calculate_average_rating(novel_id)
    novel = Novel.query.get(novel_id)
    novel.user_rating = average_rating
    db.session.commit()
    
    return redirect(url_for('novels.detail', id=novel_id))


@ratings_bp.route('/novels/<int:novel_id>/rate/delete', methods=['POST'])
@login_required
def delete_rating(novel_id):
    user_id = session.get('user_id', 1)
    
    rating = Rating.query.filter_by(user_id=user_id, novel_id=novel_id).first()
    if rating:
        db.session.delete(rating)
        db.session.commit()
        
        average_rating = calculate_average_rating(novel_id)
        novel = Novel.query.get(novel_id)
        novel.user_rating = average_rating
        db.session.commit()
    
    return redirect(url_for('novels.detail', id=novel_id))