import pytest
from app import create_app
from app.models import db, User, Category, Novel, Chapter, ChapterRule, NovelChapterRule, Tag, Favorite, Rating, ReadingProgress, Bookmark


class TestUserModel:
    def test_user_creation(self, app):
        with app.app_context():
            user = User(username='testuser', password='testpass123')
            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.username == 'testuser'
            assert user.created_at is not None

    def test_user_password_hash(self, app):
        with app.app_context():
            user = User(username='testuser', password='testpass123')
            assert user.password_hash is not None
            assert user.password_hash != 'testpass123'

    def test_user_password_check(self, app):
        with app.app_context():
            user = User(username='testuser', password='testpass123')
            assert user.check_password('testpass123') is True
            assert user.check_password('wrongpass') is False


class TestCategoryModel:
    def test_category_creation(self, app):
        with app.app_context():
            category = Category(name='玄幻', description='玄幻小说')
            db.session.add(category)
            db.session.commit()

            assert category.id is not None
            assert category.name == '玄幻'
            assert category.description == '玄幻小说'

    def test_category_default_sort_order(self, app):
        with app.app_context():
            category = Category(name='科幻')
            db.session.add(category)
            db.session.commit()

            assert category.sort_order == 0


class TestNovelModel:
    def test_novel_creation(self, app):
        with app.app_context():
            category = Category(name='玄幻')
            db.session.add(category)
            db.session.commit()

            novel = Novel(title='测试小说', author='测试作者', category_id=category.id)
            db.session.add(novel)
            db.session.commit()

            assert novel.id is not None
            assert novel.title == '测试小说'
            assert novel.author == '测试作者'
            assert novel.category_id == category.id

    def test_novel_user_rating_default(self, app):
        with app.app_context():
            novel = Novel(title='测试小说')
            db.session.add(novel)
            db.session.commit()

            assert novel.user_rating == 0

    def test_novel_author_optional(self, app):
        with app.app_context():
            novel = Novel(title='测试小说')
            db.session.add(novel)
            db.session.commit()

            assert novel.author is None


class TestChapterModel:
    def test_chapter_creation(self, app):
        with app.app_context():
            novel = Novel(title='测试小说')
            db.session.add(novel)
            db.session.commit()

            chapter = Chapter(novel_id=novel.id, title='第一章 开始', content='这是第一章内容', order=1)
            db.session.add(chapter)
            db.session.commit()

            assert chapter.id is not None
            assert chapter.title == '第一章 开始'
            assert chapter.content == '这是第一章内容'
            assert chapter.order == 1

    def test_chapter_order(self, app):
        with app.app_context():
            novel = Novel(title='测试小说')
            db.session.add(novel)
            db.session.commit()

            ch1 = Chapter(novel_id=novel.id, title='第一章', content='内容1', order=1)
            ch2 = Chapter(novel_id=novel.id, title='第二章', content='内容2', order=2)
            db.session.add_all([ch1, ch2])
            db.session.commit()

            chapters = Chapter.query.filter_by(novel_id=novel.id).order_by(Chapter.order).all()
            assert chapters[0].order == 1
            assert chapters[1].order == 2


class TestChapterRuleModel:
    def test_rule_creation(self, app):
        with app.app_context():
            rule = ChapterRule(name='中文数字章节', pattern='^第[零一二三四五六七八九十百千万\\d]+章.*$', category='中文序号')
            db.session.add(rule)
            db.session.commit()

            assert rule.id is not None
            assert rule.name == '中文数字章节'
            assert rule.pattern == '^第[零一二三四五六七八九十百千万\\d]+章.*$'
            assert rule.category == '中文序号'

    def test_rule_enabled_default(self, app):
        with app.app_context():
            rule = ChapterRule(name='测试规则', pattern='^测试$', category='chinese-number')
            db.session.add(rule)
            db.session.commit()

            assert rule.enabled is True


class TestNovelChapterRuleModel:
    def test_novel_rule_creation(self, app):
        with app.app_context():
            novel = Novel(title='测试小说')
            db.session.add(novel)
            db.session.commit()

            rule = NovelChapterRule(novel_id=novel.id, pattern='^自定义规则$', description='自定义章节规则')
            db.session.add(rule)
            db.session.commit()

            assert rule.id is not None
            assert rule.novel_id == novel.id
            assert rule.pattern == '^自定义规则$'

    def test_novel_rule_novel_relation(self, app):
        with app.app_context():
            novel = Novel(title='测试小说')
            db.session.add(novel)
            db.session.commit()

            rule = NovelChapterRule(novel_id=novel.id, pattern='^规则$')
            db.session.add(rule)
            db.session.commit()

            retrieved_rule = NovelChapterRule.query.filter_by(novel_id=novel.id).first()
            assert retrieved_rule is not None
            assert retrieved_rule.id == rule.id


class TestTagModel:
    def test_tag_creation(self, app):
        with app.app_context():
            tag = Tag(name='爽文', color='#FF6600')
            db.session.add(tag)
            db.session.commit()

            assert tag.id is not None
            assert tag.name == '爽文'
            assert tag.color == '#FF6600'

    def test_tag_color_default(self, app):
        with app.app_context():
            tag = Tag(name='测试标签')
            db.session.add(tag)
            db.session.commit()

            assert tag.color is not None


class TestFavoriteModel:
    def test_favorite_creation(self, app):
        with app.app_context():
            user = User(username='testuser', password='testpass123')
            novel = Novel(title='测试小说')
            db.session.add_all([user, novel])
            db.session.commit()

            favorite = Favorite(user_id=user.id, novel_id=novel.id)
            db.session.add(favorite)
            db.session.commit()

            assert favorite.id is not None
            assert favorite.user_id == user.id
            assert favorite.novel_id == novel.id


class TestRatingModel:
    def test_rating_creation(self, app):
        with app.app_context():
            user = User(username='testuser', password='testpass123')
            novel = Novel(title='测试小说')
            db.session.add_all([user, novel])
            db.session.commit()

            rating = Rating(user_id=user.id, novel_id=novel.id, score=4, comment='很好看')
            db.session.add(rating)
            db.session.commit()

            assert rating.id is not None
            assert rating.score == 4
            assert rating.comment == '很好看'

    def test_rating_score_range(self, app):
        with app.app_context():
            user = User(username='testuser', password='testpass123')
            novel = Novel(title='测试小说')
            db.session.add_all([user, novel])
            db.session.commit()

            rating = Rating(user_id=user.id, novel_id=novel.id, score=1)
            db.session.add(rating)
            db.session.commit()
            assert rating.score == 1

            rating2 = Rating(user_id=user.id, novel_id=novel.id, score=5)
            db.session.add(rating2)
            db.session.commit()
            assert rating2.score == 5


class TestReadingProgressModel:
    def test_progress_creation(self, app):
        with app.app_context():
            user = User(username='testuser', password='testpass123')
            novel = Novel(title='测试小说')
            db.session.add_all([user, novel])
            db.session.commit()

            chapter = Chapter(novel_id=novel.id, title='第一章', content='内容', order=1)
            db.session.add(chapter)
            db.session.commit()

            progress = ReadingProgress(user_id=user.id, novel_id=novel.id, chapter_id=chapter.id, scroll_position=500)
            db.session.add(progress)
            db.session.commit()

            assert progress.id is not None
            assert progress.scroll_position == 500


class TestBookmarkModel:
    def test_bookmark_creation(self, app):
        with app.app_context():
            user = User(username='testuser', password='testpass123')
            novel = Novel(title='测试小说')
            db.session.add_all([user, novel])
            db.session.commit()

            chapter = Chapter(novel_id=novel.id, title='第一章', content='内容', order=1)
            db.session.add(chapter)
            db.session.commit()

            bookmark = Bookmark(user_id=user.id, novel_id=novel.id, chapter_id=chapter.id, title='精彩段落', position=100)
            db.session.add(bookmark)
            db.session.commit()

            assert bookmark.id is not None
            assert bookmark.title == '精彩段落'
            assert bookmark.position == 100