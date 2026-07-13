from flask import Blueprint, Response
from app.models import Novel, Chapter
from app.auth import login_required

export_bp = Blueprint('export', __name__)


@export_bp.route('/novels/<int:novel_id>/export')
@login_required
def export_novel(novel_id):
    novel = Novel.query.get_or_404(novel_id)
    chapters = Chapter.query.filter_by(novel_id=novel_id).order_by(Chapter.order).all()

    lines = [novel.title, '']
    for ch in chapters:
        lines.append(ch.title)
        lines.append('')
        lines.append(ch.content)
        lines.append('')

    content = '\n'.join(lines)

    return Response(
        content,
        mimetype='text/plain; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename="{novel.title}.txt"'
        }
    )