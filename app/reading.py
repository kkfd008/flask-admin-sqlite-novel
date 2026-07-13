from flask import Blueprint, render_template, request, jsonify, session
from app.models import db, Novel, Chapter, ReadingProgress, Bookmark
from app.auth import login_required

reading_bp = Blueprint('reading', __name__)


@reading_bp.route('/novels/<int:novel_id>/read/<int:chapter_id>')
@login_required
def read_chapter(novel_id, chapter_id):
    novel = Novel.query.get_or_404(novel_id)
    chapter = Chapter.query.get_or_404(chapter_id)

    chapters = Chapter.query.filter_by(novel_id=novel_id).order_by(Chapter.order).all()
    current_index = next((i for i, ch in enumerate(chapters) if ch.id == chapter_id), 0)
    prev_chapter = chapters[current_index - 1] if current_index > 0 else None
    next_chapter = chapters[current_index + 1] if current_index < len(chapters) - 1 else None

    return render_template('reading/reader.html', novel=novel, chapter=chapter,
                          prev_chapter=prev_chapter, next_chapter=next_chapter)


@reading_bp.route('/api/progress', methods=['POST'])
@login_required
def save_progress():
    user_id = session.get('user_id')
    data = request.get_json()

    progress = ReadingProgress.query.filter_by(user_id=user_id, novel_id=data['novel_id']).first()
    if progress:
        progress.chapter_id = data['chapter_id']
        progress.scroll_position = data['scroll_position']
    else:
        progress = ReadingProgress(
            user_id=user_id,
            novel_id=data['novel_id'],
            chapter_id=data['chapter_id'],
            scroll_position=data['scroll_position']
        )
        db.session.add(progress)
    db.session.commit()

    return jsonify({'status': 'ok'})


@reading_bp.route('/api/bookmark', methods=['POST'])
@login_required
def add_bookmark():
    user_id = session.get('user_id')
    data = request.get_json()

    bookmark = Bookmark(
        user_id=user_id,
        novel_id=data['novel_id'],
        chapter_id=data['chapter_id'],
        title=data['title'],
        position=data['position']
    )
    db.session.add(bookmark)
    db.session.commit()

    return jsonify({'status': 'ok', 'id': bookmark.id})


@reading_bp.route('/api/bookmark/<int:bookmark_id>/delete', methods=['POST'])
@login_required
def delete_bookmark(bookmark_id):
    user_id = session.get('user_id')
    bookmark = Bookmark.query.filter_by(id=bookmark_id, user_id=user_id).first()
    if bookmark:
        db.session.delete(bookmark)
        db.session.commit()
    return jsonify({'status': 'ok'})