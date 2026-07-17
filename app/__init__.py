from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose
from flask_session import Session
import os
import sqlite3
from flask_admin.contrib.sqla import ModelView

db = SQLAlchemy()


class AdminDashboardView(AdminIndexView):
    @expose('/')
    def index(self):
        from app.models import User, Novel, Chapter, Category, Tag, Favorite, Rating, ChapterRule, NovelChapterRule
        stats = {
            'users': User.query.count(),
            'novels': Novel.query.count(),
            'chapters': Chapter.query.count(),
            'categories': Category.query.count(),
            'tags': Tag.query.count(),
            'favorites': Favorite.query.count(),
            'ratings': Rating.query.count(),
            'chapter_rules': ChapterRule.query.count(),
            'novel_chapter_rules': NovelChapterRule.query.count(),
        }
        return self.render('admin/index.html', stats=stats)


def _migrate_db(app):
    """Add missing columns to existing tables."""
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    if not os.path.isabs(db_path):
        db_path = os.path.join(app.instance_path, db_path)
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Upload: file_size
    cursor.execute("PRAGMA table_info(upload)")
    upload_cols = [row[1] for row in cursor.fetchall()]
    if not upload_cols:
        conn.close()
        return
    if 'file_size' not in upload_cols:
        cursor.execute("ALTER TABLE upload ADD COLUMN file_size INTEGER DEFAULT 0")
    if 'novel_id' not in upload_cols:
        cursor.execute("ALTER TABLE upload ADD COLUMN novel_id INTEGER DEFAULT 0")

    conn.commit()
    conn.close()


class AuthModelView(ModelView):
    def is_accessible(self):
        from flask import session
        return 'user_id' in session

    def inaccessible_callback(self, name, **kwargs):
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))


class NovelAdmin(AuthModelView):
    column_list = ('id', 'title', 'author', 'category', 'word_count', 'chapter_count', 'created_at')
    column_labels = {
        'id': 'ID',
        'title': '书名',
        'author': '作者',
        'category': '分类',
        'word_count': '字数',
        'chapter_count': '章节数',
        'created_at': '创建时间',
    }
    column_searchable_list = ('title', 'author')
    column_filters = ('category',)
    page_size = 20


def create_app(config=None):
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/novel.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if config:
        app.config.update(config)

    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'flask_session')
    app.config['SESSION_PERMANENT'] = False
    Session(app)

    db.init_app(app)

    _migrate_db(app)

    from app.auth import auth_bp
    from app.categories import categories_bp
    from app.tags import tags_bp
    from app.rules import rules_bp
    from app.novels import novels_bp
    from app.ratings import ratings_bp
    from app.favorites import favorites_bp
    from app.export import export_bp
    from app.search import search_bp
    from app.reading import reading_bp
    from app.editor import editor_bp
    from app.importer import importer_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(rules_bp)
    app.register_blueprint(novels_bp)
    app.register_blueprint(ratings_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(reading_bp)
    app.register_blueprint(editor_bp)
    app.register_blueprint(importer_bp)

    admin = Admin(
        app,
        name='墨斋 · 管理',
        index_view=AdminDashboardView(),
    )

    from app.models import User, Category, Novel, Chapter, ChapterRule, NovelChapterRule, Tag, Favorite, Rating, ReadingProgress, Bookmark, Upload

    @app.context_processor
    def inject_has_uploads():
        return {'has_uploads': db.session.query(Upload.query.exists()).scalar()}

    admin.add_view(AuthModelView(User, db.session))
    admin.add_view(AuthModelView(Category, db.session))
    admin.add_view(NovelAdmin(Novel, db.session))
    admin.add_view(AuthModelView(Chapter, db.session))
    admin.add_view(AuthModelView(ChapterRule, db.session))
    admin.add_view(AuthModelView(NovelChapterRule, db.session))
    admin.add_view(AuthModelView(Tag, db.session))
    admin.add_view(AuthModelView(Favorite, db.session))
    admin.add_view(AuthModelView(Rating, db.session))
    admin.add_view(AuthModelView(ReadingProgress, db.session))
    admin.add_view(AuthModelView(Bookmark, db.session))

    return app