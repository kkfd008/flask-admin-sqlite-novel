from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_session import Session
import os
from flask_admin.contrib.sqla import ModelView

db = SQLAlchemy()


class AuthModelView(ModelView):
    def is_accessible(self):
        from flask import session
        return 'user_id' in session

    def inaccessible_callback(self, name, **kwargs):
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))


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

    admin = Admin(app, name='Novel Admin')

    from app.models import User, Category, Novel, Chapter, ChapterRule, NovelChapterRule, Tag, Favorite, Rating, ReadingProgress, Bookmark, Upload

    @app.context_processor
    def inject_has_uploads():
        return {'has_uploads': db.session.query(Upload.query.exists()).scalar()}

    admin.add_view(AuthModelView(User, db.session))
    admin.add_view(AuthModelView(Category, db.session))
    admin.add_view(AuthModelView(Novel, db.session))
    admin.add_view(AuthModelView(Chapter, db.session))
    admin.add_view(AuthModelView(ChapterRule, db.session))
    admin.add_view(AuthModelView(NovelChapterRule, db.session))
    admin.add_view(AuthModelView(Tag, db.session))
    admin.add_view(AuthModelView(Favorite, db.session))
    admin.add_view(AuthModelView(Rating, db.session))
    admin.add_view(AuthModelView(ReadingProgress, db.session))
    admin.add_view(AuthModelView(Bookmark, db.session))

    return app