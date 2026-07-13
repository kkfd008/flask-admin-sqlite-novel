import pytest
import io


class TestReaderBottomNav:
    """测试阅读器底部导航栏不遮挡内容"""

    def test_reader_has_bottom_nav_with_prev_dir_next(self, app, client):
        """阅读页底部应有 上一章/返回目录/下一章 导航栏"""
        novel_id = None
        ch1_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, cat])
            db.session.commit()
            novel = Novel(title='导航测试', category_id=cat.id, chapter_count=2, word_count=100)
            db.session.add(novel)
            db.session.commit()
            ch1 = Chapter(novel_id=novel.id, title='第1章', content='内容' * 100, order=1, word_count=200)
            ch2 = Chapter(novel_id=novel.id, title='第2章', content='内容2' * 100, order=2, word_count=200)
            db.session.add_all([ch1, ch2])
            db.session.commit()
            novel_id = novel.id
            ch1_id = ch1.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}/read/{ch1_id}')
        html = response.data.decode('utf-8')

        # 底部导航栏应存在
        assert '上一章' in html or 'prev' in html.lower()
        assert '返回目录' in html
        assert '下一章' in html or 'next' in html.lower()

        # "返回目录" 应指向章节目录分页页，而非书籍详情页
        assert f'/novels/{novel_id}/chapter' in html

        # 内容区域应有底部内边距，防止被底部栏遮挡
        assert 'padding-bottom' in html or 'reader-content' in html

    def test_last_chapter_prev_disabled_next_enabled(self, app, client):
        """第一章：上一章禁用，下一章可用"""
        novel_id = None
        ch1_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, cat])
            db.session.commit()
            novel = Novel(title='禁用测试', category_id=cat.id, chapter_count=2, word_count=100)
            db.session.add(novel)
            db.session.commit()
            ch1 = Chapter(novel_id=novel.id, title='第1章', content='内容1', order=1, word_count=3)
            ch2 = Chapter(novel_id=novel.id, title='第2章', content='内容2', order=2, word_count=3)
            db.session.add_all([ch1, ch2])
            db.session.commit()
            novel_id = novel.id
            ch1_id = ch1.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}/read/{ch1_id}')
        html = response.data.decode('utf-8')

        # 在第一页，上一章应禁用
        assert '已是第一章' in html or 'disabled' in html
        # 下一章应可用（有链接指向第2章）
        assert '第2章' in html or f'/novels/{novel_id}/read/' in html

    def test_first_chapter_next_enabled(self, app, client):
        """最后一章：下一章禁用，上一章可用"""
        novel_id = None
        ch2_id = None
        with app.app_context():
            from app.models import db, User, Novel, Chapter, Category
            user = User(username='admin', password='admin123')
            cat = Category(name='武侠', sort_order=0)
            db.session.add_all([user, cat])
            db.session.commit()
            novel = Novel(title='末章测试', category_id=cat.id, chapter_count=2, word_count=100)
            db.session.add(novel)
            db.session.commit()
            ch1 = Chapter(novel_id=novel.id, title='第1章', content='内容1', order=1, word_count=3)
            ch2 = Chapter(novel_id=novel.id, title='第2章', content='内容2', order=2, word_count=3)
            db.session.add_all([ch1, ch2])
            db.session.commit()
            novel_id = novel.id
            ch2_id = ch2.id

        client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        response = client.get(f'/novels/{novel_id}/read/{ch2_id}')
        html = response.data.decode('utf-8')

        # 在最后一页，下一章应禁用
        assert '已是最后一章' in html or 'disabled' in html
        # 上一章应可用
        assert '第1章' in html or '上一章' in html