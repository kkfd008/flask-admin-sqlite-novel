from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config=None):
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/novel.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if config:
        app.config.update(config)

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

    return app