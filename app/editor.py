from flask import Blueprint, render_template, redirect, url_for, request
from app.models import db, Novel, Chapter
from app.auth import login_required

editor_bp = Blueprint('editor', __name__)


@editor_bp.route('/novels/<int:novel_id>/chapter/<int:chapter_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_chapter(novel_id, chapter_id):
    novel = Novel.query.get_or_404(novel_id)
    chapter = Chapter.query.get_or_404(chapter_id)

    if request.method == 'POST':
        chapter.title = request.form.get('title')
        chapter.content = request.form.get('content')
        db.session.commit()
        return redirect(url_for('reading.read_chapter', novel_id=novel_id, chapter_id=chapter_id))

    return render_template('editor/edit.html', novel=novel, chapter=chapter)