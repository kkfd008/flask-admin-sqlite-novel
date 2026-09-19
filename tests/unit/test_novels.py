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


class TestNovelSearchAndSort:
    def _seed_novels(self, app):
        """创建 3 本书：标题、作者、章节数各不相同，便于验证搜索与排序"""
        with app.app_context():
            from app.models import db, User, Novel
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()
            db.session.add_all([
                Novel(title='剑来', author='烽火戏诸侯', chapter_count=10),
                Novel(title='雪中悍刀行', author='烽火戏诸侯', chapter_count=30),
                Novel(title='三体', author='刘慈欣', chapter_count=20),
            ])
            db.session.commit()

    def test_search_by_title_filters_results(self, app, client):
        """按书名搜索时，只显示匹配的书"""
        self._seed_novels(app)
        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/novels/?q=三体')
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        assert '三体' in html, '匹配的书名应显示'
        assert '雪中悍刀行' not in html, '不匹配的书不应显示'

    def test_search_by_author_filters_results(self, app, client):
        """按作者搜索时，只显示该作者的书"""
        self._seed_novels(app)
        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/novels/?q=刘慈欣')
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        assert '三体' in html, '该作者的书应显示'
        assert '雪中悍刀行' not in html, '其他作者的书不应显示'

    def test_sort_by_chapter_count_desc(self, app, client):
        """按章节数降序：章节数多的书排在前面"""
        self._seed_novels(app)
        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/novels/?sort_by=chapter_count&sort_order=desc')
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        pos_most = html.find('雪中悍刀行')   # 30 章
        pos_least = html.find('剑来')        # 10 章
        assert pos_most != -1 and pos_least != -1, '两本书都应显示'
        assert pos_most < pos_least, '章节数多的书应排在前面'

    def test_sort_by_chapter_count_asc(self, app, client):
        """按章节数升序：章节数少的书排在前面"""
        self._seed_novels(app)
        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

        response = client.get('/novels/?sort_by=chapter_count&sort_order=asc')
        assert response.status_code == 200
        html = response.data.decode('utf-8')

        pos_least = html.find('剑来')        # 10 章
        pos_most = html.find('雪中悍刀行')   # 30 章
        assert pos_least != -1 and pos_most != -1, '两本书都应显示'
        assert pos_least < pos_most, '章节数少的书应排在前面'


class TestSortRememberedInSession:
    """书架页的排序选择用 session 记忆，并回显在下拉框中。"""

    def _seed_novels(self, app):
        with app.app_context():
            from app.models import db, User, Novel
            user = User(username='admin', password='admin123')
            db.session.add(user)
            db.session.commit()
            db.session.add_all([
                Novel(title='甲书', word_count=300),
                Novel(title='乙书', word_count=100),
                Novel(title='丙书', word_count=200),
            ])
            db.session.commit()

    def _login(self, client):
        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

    def test_sort_selection_is_remembered(self, app, client):
        """不带参数再次访问时，下拉框应回显上次的选择。"""
        self._seed_novels(app)
        self._login(client)

        client.get('/novels/?sort_by=word_count&sort_order=asc')

        html = client.get('/novels/').data.decode('utf-8')
        assert 'value="word_count" selected' in html, '排序下拉应回显上次选择'
        assert 'value="asc" selected' in html, '升降序下拉应回显上次选择'

    def test_remembered_sort_is_applied(self, app, client):
        """不带参数再次访问时，应按记忆的排序呈现结果。"""
        self._seed_novels(app)
        self._login(client)

        client.get('/novels/?sort_by=word_count&sort_order=asc')

        html = client.get('/novels/').data.decode('utf-8')
        pos_yi = html.find('乙书')    # 100 字
        pos_bing = html.find('丙书')  # 200 字
        pos_jia = html.find('甲书')   # 300 字
        assert pos_yi != -1 and pos_bing != -1 and pos_jia != -1, '三本书都应显示'
        assert pos_yi < pos_bing < pos_jia, '应沿用记忆的按字数升序'

    def test_explicit_param_overrides_remembered_sort(self, app, client):
        """显式传入排序参数时应覆盖记忆值。"""
        self._seed_novels(app)
        self._login(client)

        client.get('/novels/?sort_by=word_count&sort_order=asc')
        html = client.get('/novels/?sort_by=title&sort_order=desc').data.decode('utf-8')

        assert 'value="title" selected' in html
        assert 'value="desc" selected' in html
        assert 'value="word_count" selected' not in html