from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

novel_tags = db.Table('novel_tags',
    db.Column('novel_id', db.Integer, db.ForeignKey('novel.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(500))
    sort_order = db.Column(db.Integer, default=0)


class Novel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255))
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    word_count = db.Column(db.Integer, default=0)
    chapter_count = db.Column(db.Integer, default=0)
    user_rating = db.Column(db.Integer, nullable=False, default=0)
    cover = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    tags = db.relationship('Tag', secondary=novel_tags, backref=db.backref('novels', lazy='dynamic'))
    category = db.relationship('Category', backref=db.backref('novels', lazy='dynamic'))


class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    novel_id = db.Column(db.Integer, db.ForeignKey('novel.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, nullable=False, default=0)
    word_count = db.Column(db.Integer, default=0)

    novel = db.relationship('Novel', backref=db.backref('chapters', lazy='dynamic'))


class ChapterRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    pattern = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    description = db.Column(db.String(500))
    sort_order = db.Column(db.Integer, default=0)


class NovelChapterRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    novel_id = db.Column(db.Integer, db.ForeignKey('novel.id'), nullable=False, unique=True)
    pattern = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    novel = db.relationship('Novel', backref=db.backref('chapter_rule', uselist=False))


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    color = db.Column(db.String(20), default='#1E9FFF')


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    novel_id = db.Column(db.Integer, db.ForeignKey('novel.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('favorites', lazy='dynamic'))
    novel = db.relationship('Novel', backref=db.backref('favorites', lazy='dynamic'))


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    novel_id = db.Column(db.Integer, db.ForeignKey('novel.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', backref=db.backref('ratings', lazy='dynamic'))
    novel = db.relationship('Novel', backref=db.backref('ratings', lazy='dynamic'))


class ReadingProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    novel_id = db.Column(db.Integer, db.ForeignKey('novel.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'))
    scroll_position = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    user = db.relationship('User', backref=db.backref('reading_progress', lazy='dynamic'))
    novel = db.relationship('Novel', backref=db.backref('reading_progress', lazy='dynamic'))
    chapter = db.relationship('Chapter')


class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    novel_id = db.Column(db.Integer, db.ForeignKey('novel.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'))
    title = db.Column(db.String(255), nullable=False)
    position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', backref=db.backref('bookmarks', lazy='dynamic'))
    novel = db.relationship('Novel', backref=db.backref('bookmarks', lazy='dynamic'))
    chapter = db.relationship('Chapter')


class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.String(500))
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    novel_id = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    last_import_at = db.Column(db.DateTime)