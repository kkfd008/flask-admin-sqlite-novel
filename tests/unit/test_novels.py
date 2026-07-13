import pytest


class TestNovelDelete:
    def test_delete_novel_with_chapters_succeeds(self, app, client):
        """删除有章节的小说应成功，不报 IntegrityError"""
        with app.app_context():
            from app.models import db, User, Novel, Chapter, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, cat])
            db.session.commit()

            novel = Novel(title='测试小说', author='作者', category_id=cat.id)
            db.session.add(novel)
            db.session.commit()

            ch1 = Chapter(novel_id=novel.id, title='第1章', content='内容1', order=1, word_count=3)
            ch2 = Chapter(novel_id=novel.id, title='第2章', content='内容2', order=2, word_count=3)
            db.session.add_all([ch1, ch2])
            db.session.commit()

            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel_id}/delete', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import Novel, Chapter
            novel = Novel.query.get(novel_id)
            assert novel is None, '小说应已被删除'
            chapters = Chapter.query.filter_by(novel_id=novel_id).all()
            assert len(chapters) == 0, '章节应已被级联删除'

    def test_delete_novel_cleans_all_related_data(self, app, client):
        """删除小说应清理所有关联数据（章节、收藏、评分、书签、阅读进度）"""
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter, Category, Favorite, Rating, Bookmark, ReadingProgress
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, cat])
            db.session.commit()

            novel = Novel(title='关联小说', author='作者', category_id=cat.id)
            db.session.add(novel)
            db.session.commit()

            ch = Chapter(novel_id=novel.id, title='第1章', content='内容', order=1, word_count=2)
            fav = Favorite(user_id=user.id, novel_id=novel.id)
            rating = Rating(user_id=user.id, novel_id=novel.id, score=5)
            bm = Bookmark(user_id=user.id, novel_id=novel.id, chapter_id=ch.id, title='书签')
            progress = ReadingProgress(user_id=user.id, novel_id=novel.id, chapter_id=ch.id)
            db.session.add_all([ch, fav, rating, bm, progress])
            db.session.commit()

            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.post(f'/novels/{novel_id}/delete', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from app.models import Novel, Chapter, Favorite, Rating, Bookmark, ReadingProgress
            assert Novel.query.get(novel_id) is None
            assert Chapter.query.filter_by(novel_id=novel_id).count() == 0
            assert Favorite.query.filter_by(novel_id=novel_id).count() == 0
            assert Rating.query.filter_by(novel_id=novel_id).count() == 0
            assert Bookmark.query.filter_by(novel_id=novel_id).count() == 0
            assert ReadingProgress.query.filter_by(novel_id=novel_id).count() == 0