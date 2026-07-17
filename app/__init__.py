from flask import Flask, request, session as flask_session
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_session import Session
from flask_babel import Babel, lazy_gettext as _l
import os
import sqlite3
from werkzeug.security import generate_password_hash
from wtforms import PasswordField

db = SQLAlchemy()

# ── Babel config ──
SUPPORTED_LOCALES = ['zh', 'en']


def get_locale():
    lang = flask_session.get('lang')
    if lang in SUPPORTED_LOCALES:
        return lang
    return request.accept_languages.best_match(SUPPORTED_LOCALES, 'zh')


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
        return 'user_id' in flask_session

    def inaccessible_callback(self, name, **kwargs):
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))


class UserAdmin(AuthModelView):
    """Custom user admin: hide password_hash, only allow password changes."""
    column_list = ('id', 'username', 'created_at')
    column_labels = {
        'id': 'ID',
        'username': '用户名',
        'created_at': '创建时间',
    }
    column_searchable_list = ('username',)
    page_size = 20

    # Replace password_hash with a plaintext password field
    form_excluded_columns = ('password_hash',)
    form_extra_fields = {
        'password': PasswordField('密码'),
    }
    form_create_rules = ('username', 'password')
    form_edit_rules = ('password',)

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password_hash = generate_password_hash(form.password.data)


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


class CategoryAdmin(AuthModelView):
    column_labels = {
        'id': 'ID', 'name': '名称', 'description': '描述',
        'sort_order': '排序',
    }
    column_searchable_list = ('name',)


class ChapterAdmin(AuthModelView):
    column_list = ('id', 'title', 'novel', 'order', 'word_count')
    column_labels = {
        'id': 'ID', 'title': '标题', 'novel': '小说',
        'order': '序号', 'word_count': '字数',
    }
    column_searchable_list = ('title',)


class ChapterRuleAdmin(AuthModelView):
    column_labels = {
        'id': 'ID', 'name': '名称', 'pattern': '匹配模式',
        'description': '描述',
    }
    column_searchable_list = ('name', 'pattern')


class NovelChapterRuleAdmin(AuthModelView):
    column_labels = {
        'id': 'ID', 'novel': '小说', 'chapter_rule': '章节规则',
    }


class TagAdmin(AuthModelView):
    column_labels = {'id': 'ID', 'name': '名称', 'color': '颜色'}
    column_searchable_list = ('name',)


class RatingAdmin(AuthModelView):
    column_labels = {
        'id': 'ID', 'novel': '小说', 'user': '用户',
        'score': '评分', 'comment': '评论', 'created_at': '创建时间',
    }


class FavoriteAdmin(AuthModelView):
    column_labels = {
        'id': 'ID', 'novel': '小说', 'user': '用户', 'created_at': '收藏时间',
    }


class ReadingProgressAdmin(AuthModelView):
    column_labels = {
        'id': 'ID', 'user': '用户', 'novel': '小说',
        'chapter': '章节', 'position': '阅读位置', 'updated_at': '更新时间',
    }


class BookmarkAdmin(AuthModelView):
    column_labels = {
        'id': 'ID', 'user': '用户', 'novel': '小说',
        'chapter': '章节', 'note': '备注', 'created_at': '创建时间',
    }


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

    # i18n
    babel = Babel(app, locale_selector=get_locale)

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

    # Language switch route
    @app.route('/admin/lang/<lang>')
    def set_lang(lang):
        if lang in SUPPORTED_LOCALES:
            flask_session['lang'] = lang
        from flask import redirect
        return redirect(request.referrer or '/admin/')

    admin = Admin(
        app,
        name='墨斋 · 管理',
        index_view=AdminDashboardView(),
    )

    from app.models import User, Category, Novel, Chapter, ChapterRule, NovelChapterRule, Tag, Favorite, Rating, ReadingProgress, Bookmark

    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(CategoryAdmin(Category, db.session))
    admin.add_view(NovelAdmin(Novel, db.session))
    admin.add_view(ChapterAdmin(Chapter, db.session))
    admin.add_view(ChapterRuleAdmin(ChapterRule, db.session))
    admin.add_view(NovelChapterRuleAdmin(NovelChapterRule, db.session))
    admin.add_view(TagAdmin(Tag, db.session))
    admin.add_view(FavoriteAdmin(Favorite, db.session))
    admin.add_view(RatingAdmin(Rating, db.session))
    admin.add_view(ReadingProgressAdmin(ReadingProgress, db.session))
    admin.add_view(BookmarkAdmin(Bookmark, db.session))

    return app