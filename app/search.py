from flask import Blueprint, render_template, request
from app.models import Chapter, Novel
from app.auth import login_required

search_bp = Blueprint('search', __name__, url_prefix='/search')


@search_bp.route('')
@login_required
def search():
    q = request.args.get('q', '')
    results = []

    if q:
        chapters = Chapter.query.filter(Chapter.content.like(f'%{q}%')).all()
        for ch in chapters:
            novel = Novel.query.get(ch.novel_id)
            pos = ch.content.find(q)
            snippet_start = max(0, pos - 20)
            snippet_end = min(len(ch.content), pos + len(q) + 80)
            snippet = ch.content[snippet_start:snippet_end]
            results.append({
                'novel_title': novel.title,
                'novel_id': novel.id,
                'chapter_title': ch.title,
                'chapter_id': ch.id,
                'snippet': snippet
            })

    return render_template('search/results.html', results=results, query=q)