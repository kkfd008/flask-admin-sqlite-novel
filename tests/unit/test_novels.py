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


class TestNovelEdit:
    def test_detail_page_has_edit_button(self, app, client):
        """小说详情页应有修改按钮"""
        novel_id = None
        with app.app_context():
            from app.models import db, User, Novel, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, cat])
            db.session.commit()

            novel = Novel(title='测试小说', author='作者', category_id=cat.id)
            db.session.add(novel)
            db.session.commit()
            novel_id = novel.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get(f'/novels/{novel_id}', follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # 应有修改按钮
        assert '修改' in html, f'详情页应有修改按钮，实际: {html[:500]}'

    def test_edit_novel_updates_title_author_category(self, app, client):
        """修改小说可更新标题、作者、分类"""
        novel_id = None
        cat1_id = None
        cat2_id = None
        with app.app_context():
            from app.models import db, User, Novel, Category
            user = User(username='admin', password='admin123')
            cat1 = Category(name='武侠', sort_order=0)
            cat2 = Category(name='科幻', sort_order=1)
            db.session.add_all([user, cat1, cat2])
            db.session.commit()

            novel = Novel(title='原书名', author='原作者', category_id=cat1.id)
            db.session.add(novel)
            db.session.commit()
            novel_id = novel.id
            cat1_id = cat1.id
            cat2_id = cat2.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        # 提交修改
        response = client.post(f'/novels/{novel_id}/edit', data={
            'title': '新书名',
            'author': '新作者',
            'category_id': str(cat2_id),
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Novel
            novel = Novel.query.get(novel_id)
            assert novel is not None
            assert novel.title == '新书名', f'标题应为新书名，实际: {novel.title}'
            assert novel.author == '新作者', f'作者应为新作者，实际: {novel.author}'
            assert novel.category_id == cat2_id, f'分类应为科幻，实际: {novel.category_id}'

    def test_edit_novel_empty_category_allowed(self, app, client):
        """修改小说时分类可为空"""
        novel_id = None
        cat_id = None
        with app.app_context():
            from app.models import db, User, Novel, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, cat])
            db.session.commit()

            novel = Novel(title='原书名', author='原作者', category_id=cat.id)
            db.session.add(novel)
            db.session.commit()
            novel_id = novel.id
            cat_id = cat.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        # 提交修改，不传 category_id
        response = client.post(f'/novels/{novel_id}/edit', data={
            'title': '新书名',
            'author': '新作者',
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from app.models import Novel
            novel = Novel.query.get(novel_id)
            assert novel is not None
            assert novel.title == '新书名'
            assert novel.author == '新作者'
            assert novel.category_id is None, f'分类应为空，实际: {novel.category_id}'